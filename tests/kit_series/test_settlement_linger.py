"""Staying reachable after the settlement, and the two bounds on staying.

rerun-9 settled correctly and this process still refused two `submit_audit`
calls that arrived one and three seconds after it had gone: the exchange returns
the instant the peer's envelope lands, `run()` returned, and the private surface
the gateway forwards to was released while the peer was still talking. Nothing
was lost that time because both sides had already agreed the same digest, but
rule 35 scores a series with no agreed result 0 for both groups, so reachability
at that moment is not something to leave to timing.

The two bounds are what make it safe to stay: never past the window both sides
agreed, and no longer than the peer keeps sending.
"""

import asyncio
from typing import Any

from mars777_police.app.kit_backend_settlement import QUIET_RETRIES, BackendSettlement
from mars777_police.app.kit_greeting import KitPairing
from mars777_police.app.kit_messages import KitAuditReveal, KitResultClaim, KitRole
from mars777_police.app.kit_schedule import SUB_GAMES
from mars777_police.app.kit_settled_row import row_of
from mars777_police.app.series_consensus import consensus_scope, consensus_sha256
from mars777_police.domain.terminal import Outcome

OURS, THEIRS = "MaRs-777", "sparring-s82kma9e"
GAME_ID = f"{OURS}-vs-{THEIRS}"
RETRY = 0.01


def pairing() -> KitPairing:
    return KitPairing(GAME_ID, "uid0001", OURS, THEIRS, KitRole.THIEF, KitRole.POLICE, 6, True)


def rows() -> list[dict[str, Any]]:
    return [
        row_of(
            pairing(),
            number,
            KitRole.POLICE if number % 2 else KitRole.THIEF,
            Outcome.SURVIVAL if number % 2 else Outcome.CAPTURE,
        )
        for number in range(1, SUB_GAMES + 1)
    ]


def digest() -> str:
    return consensus_sha256(consensus_scope(GAME_ID, rows(), OURS, THEIRS))


def theirs() -> KitAuditReveal:
    return KitAuditReveal(KitRole.POLICE, (), KitResultClaim.SERIES_CONSENSUS, digest())


def settlement(window: float) -> BackendSettlement:
    async def series() -> tuple[dict[str, Any], ...]:
        return tuple(rows())

    return BackendSettlement(series_rows=series, window=window, retry=RETRY, report_series=report)


async def ignore(envelope: dict[str, Any]) -> bool:
    return True


REPORTED: list[str] = []


async def report(consensus_sha256: str) -> None:
    """Stand in for the gateway, which is where an agreed digest actually goes."""
    REPORTED.append(consensus_sha256)


def test_the_settled_side_keeps_listening_after_the_exchange_succeeds() -> None:
    """The defect itself: settling is not permission to stop being reachable."""
    polls: list[int] = []

    def received() -> KitAuditReveal | None:
        polls.append(1)
        return theirs() if len(polls) == 1 else None

    agreed = asyncio.run(settlement(5.0).settle(pairing(), KitRole.THIEF, ignore, received))

    assert agreed == digest()
    assert len(polls) == 1 + QUIET_RETRIES, "it must poll on after taking the settlement"


def test_a_peer_still_sending_keeps_us_up_and_a_quiet_one_lets_us_go() -> None:
    """The second bound: the peer's own silence is what ends the wait."""
    talkative = settlement(0.2)
    asyncio.run(talkative.settle(pairing(), KitRole.THIEF, ignore, theirs))
    assert talkative.agreed == digest()


def test_staying_never_costs_more_than_the_one_agreed_window() -> None:
    """The first bound: the exchange and the wait share a single deadline."""
    window = 0.2

    async def drive() -> float:
        loop = asyncio.get_running_loop()
        start = loop.time()
        await settlement(window).settle(pairing(), KitRole.THIEF, ignore, theirs)
        return loop.time() - start

    elapsed = asyncio.run(drive())
    assert elapsed <= window * 2, f"the wait ran past the agreed window: {elapsed:.3f}s"


def test_a_window_already_spent_adds_no_wait_at_all() -> None:
    """A settlement that consumed its window has nothing left to linger on."""

    async def drive() -> float:
        loop = asyncio.get_running_loop()
        start = loop.time()
        await settlement(0.0).settle(pairing(), KitRole.THIEF, ignore, theirs)
        return loop.time() - start

    assert asyncio.run(drive()) < 0.1


def test_the_digest_is_what_the_exchange_agreed_not_what_arrived_later() -> None:
    """Lingering is receive-only: it cannot change what the series settled on."""
    live = settlement(0.2)
    asyncio.run(live.settle(pairing(), KitRole.THIEF, ignore, theirs))
    assert live.agreed == digest()


def test_an_agreed_digest_is_reported_to_the_group() -> None:
    """The result needs the merged declaration, which no backend holds.

    So the digest travels rather than the result: the g06 owner reports what it
    agreed, and the gateway - which received Step-0 - renders the one file.
    """
    REPORTED.clear()
    live = settlement(0.2)
    asyncio.run(live.settle(pairing(), KitRole.THIEF, ignore, theirs))
    assert [digest()] == REPORTED


def test_a_series_that_agreed_nothing_reports_nothing() -> None:
    """Reporting an unmatched settlement would license a result rule 35 forbids."""
    REPORTED.clear()

    async def refused(envelope: dict[str, Any]) -> bool:
        return False

    live = settlement(0.15)
    assert asyncio.run(live.settle(pairing(), KitRole.THIEF, refused, theirs)) is None
    assert REPORTED == []
