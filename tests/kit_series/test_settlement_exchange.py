"""The settlement exchange: both directions, or the series does not settle.

The peer resends its envelope on a fixed cadence and records the series unsettled
if ours never arrives. A side that only listens therefore leaves the series in
exactly the state rule 35 scores 0 for both groups - which is why "we received
it" is not the same as "it settled".
"""

import asyncio
from typing import Any

from mars777_police.app.kit_messages import KitAuditReveal, KitResultClaim, KitRole
from mars777_police.app.kit_settlement import SettlementExchange
from mars777_police.app.series_consensus import CLAIM

DIGEST = "33f1b2032e8ce87e8bd99de82aac5ebb29943571e2ae583ce4ee2d22f2eeaf1c"


def reveal(
    sender: KitRole, digest: str | None, claim: KitResultClaim | None = None
) -> KitAuditReveal:
    return KitAuditReveal(sender, (), claim or KitResultClaim.SERIES_CONSENSUS, digest)


def exchange(answers: list[KitAuditReveal | None], sent: list[Any]) -> SettlementExchange:
    async def send(envelope: dict[str, Any]) -> None:
        sent.append(envelope)

    def received() -> KitAuditReveal | None:
        return answers.pop(0) if answers else None

    return SettlementExchange(send=send, received=received, window=0.3, retry=0.05)


def test_we_always_send_our_own_envelope() -> None:
    """The half that was missing: receiving without sending settles nothing."""
    sent: list[Any] = []
    asyncio.run(exchange([reveal(KitRole.POLICE, DIGEST)], sent).settle("thief", DIGEST))
    assert sent[0] == {
        "sender": "thief",
        "result_claim": CLAIM,
        "records": [],
        "consensus_sha": DIGEST,
    }


def test_a_matching_envelope_settles_the_series() -> None:
    sent: list[Any] = []
    agreed = asyncio.run(exchange([reveal(KitRole.POLICE, DIGEST)], sent).settle("thief", DIGEST))
    assert agreed == DIGEST


def test_a_peer_that_is_slow_is_still_a_peer_that_agrees() -> None:
    """Bounded by wall clock, not by attempts - and it keeps resending meanwhile."""
    sent: list[Any] = []
    answers: list[KitAuditReveal | None] = [None, None, reveal(KitRole.POLICE, DIGEST)]
    assert asyncio.run(exchange(answers, sent).settle("thief", DIGEST)) == DIGEST
    assert len(sent) == 3


def test_a_different_digest_does_not_settle() -> None:
    """Two honest sides that disagree about the series must not record agreement."""
    sent: list[Any] = []
    assert (
        asyncio.run(exchange([reveal(KitRole.POLICE, "b" * 64)], sent).settle("thief", DIGEST))
        is None
    )


def test_an_envelope_from_our_own_side_does_not_settle() -> None:
    sent: list[Any] = []
    assert (
        asyncio.run(exchange([reveal(KitRole.THIEF, DIGEST)], sent).settle("thief", DIGEST)) is None
    )


def test_a_sub_game_claim_does_not_settle_a_series() -> None:
    sent: list[Any] = []
    answers = [reveal(KitRole.POLICE, DIGEST, KitResultClaim.SURVIVAL)]
    assert asyncio.run(exchange(answers, sent).settle("thief", DIGEST)) is None


def test_a_silent_peer_closes_the_window_without_settling() -> None:
    """`None` is a fact about the series, not an error in this side's play."""
    sent: list[Any] = []
    assert asyncio.run(exchange([], sent).settle("thief", DIGEST)) is None
    assert sent, "we must have tried to send before giving up"


def test_the_expected_sender_follows_our_own_side() -> None:
    """Whichever side we are, the settlement we accept comes from the other one."""
    sent: list[Any] = []
    assert asyncio.run(
        exchange([reveal(KitRole.THIEF, DIGEST)], sent).settle("police", DIGEST)
    ) == (DIGEST)
    assert sent[0]["sender"] == "police"
