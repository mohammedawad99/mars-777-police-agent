"""When a series is over, and the message it is only over once we have received.

The last sub-game being disclosed is not the end. The peer sends one more
`submit_audit` - claim `series_consensus`, no records, a `consensus_sha` - and
until that has landed the series has no mutual settlement. Appendix E rule 35
scores a series with no agreed result **0 for both groups**, so the window it
arrives in is part of the game, not cleanup after it.

This was measured rather than predicted. In a real six-sub-game series both role
backends returned the moment their own last sub-game was disclosed and exited;
the gateway forwards `submit_audit` to the backend owning the live sub-game, that
port was gone, and the peer's retries had nowhere to land. Recovering it needed a
separate process standing in for a backend that should never have left.

Who waits is a property of the schedule, not of the role: whichever backend owns
sub-game 6 is the one the gateway will route the settlement to.
"""

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any, Protocol

from .kit_messages import KitAuditReveal
from .kit_schedule import SUB_GAMES
from .series_consensus import (
    agrees,
    settlement_envelope,
)


class SettlementSource(Protocol):
    """Whatever the peer's settlement is waited on, named by what it does."""

    async def await_settlement(self, timeout: float) -> KitAuditReveal:
        """Return the peer's settlement, or raise `TimeoutError` on the window."""
        ...


def plays_final_sub_game(owned: tuple[int, ...]) -> bool:
    """Whether *owned* includes the series' last sub-game, so this side waits.

    Asked of the sub-game numbers rather than of a role, because which role owns
    the final row is decided by the agreed first role and would be the wrong
    thing to hard-code on either side.
    """
    return bool(owned) and owned[-1] == SUB_GAMES


async def settlement_within(friendly: SettlementSource, window: float) -> KitAuditReveal | None:
    """The peer's series settlement, or `None` when the agreed window closed.

    A timeout is **not** absorbed into a success: returning `None` is how the
    caller learns the series ended with no mutual settlement, which is a fact
    about the game and must not be reported as a settled one.
    """
    try:
        return await friendly.await_settlement(window)
    except TimeoutError:
        return None


@dataclass(slots=True)
class SettlementExchange:
    """The two-way settlement: send ours, accept theirs only when they match.

    Both directions are required. The peer resends its envelope on a fixed
    cadence until ours arrives and then records the series unsettled if it never
    does, so a side that only listens leaves the series in exactly the state
    rule 35 scores 0 for both groups.

    Bounded by wall clock rather than by attempts: a peer that answers slowly is
    not a peer that answers wrongly, and the cap is the one both sides agreed.
    """

    send: "Callable[[dict[str, Any]], Awaitable[bool]]"
    received: "Callable[[], KitAuditReveal | None]"
    window: float
    retry: float

    async def settle(self, ours: str, digest: str) -> str | None:
        """Exchange settlements, returning the agreed digest or `None`.

        **Both directions must be proven, not one.** Concluding on the peer's
        envelope alone says "settled" while our own may never have arrived, and
        a settlement the peer never received is not a settlement - rule 35
        scores it 0 for both groups. So this returns only once our envelope has
        been positively acknowledged *and* a matching one has come back. The
        opponent found the same weakness in their own runner and fixed it; this
        is the symmetric half.

        An arrived envelope is held rather than re-read, because taking it is
        what consumes it: a peer that answered before our delivery succeeded
        must not have its answer dropped while we keep resending.

        `None` means the window closed without both facts. It is returned rather
        than raised because an unsettled series is a fact to record, not an
        error in this side's play.
        """
        envelope = settlement_envelope(ours, digest)
        theirs = "police" if ours == "thief" else "thief"
        remaining = self.window
        delivered = False
        arrived: KitAuditReveal | None = None
        while remaining > 0:
            delivered = await self.send(envelope) or delivered
            arrived = arrived or self.received()
            if delivered and arrived is not None:
                return digest if _matches(arrived, theirs, digest) else None
            await asyncio.sleep(min(self.retry, remaining))
            remaining -= self.retry
        return None


def _matches(reveal: "KitAuditReveal", sender: str, digest: str) -> bool:
    """Whether the peer's disclosure is their matching settlement, member by member."""
    return agrees(
        {
            "sender": reveal.sender.value,
            "result_claim": reveal.result_claim.value,
            "records": list(reveal.records),
            "consensus_sha": reveal.consensus_sha,
        },
        sender,
        digest,
    )
