"""What a role backend brings to settling the series it helped play.

Split from `kit_settlement` under guideline §3.2: that module owns *when* a
series settles and the exchange that settles it; this one owns what one backend
of a two-process group contributes to it. Neither has anything to say about
playing a sub-game.
"""

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any, Final

from ..infra.game_contract import consensus_retry, consensus_window
from .kit_greeting import KitPairing
from .kit_messages import KitAuditReveal, KitRole
from .kit_schedule import SUB_GAMES
from .kit_settlement import SettlementExchange
from .protocol_errors import LocalDefectError
from .series_consensus import consensus_scope, consensus_sha256

QUIET_RETRIES: Final[int] = 3
"""Consecutive silent cadences that mean the peer has stopped resending."""


async def uncollected(row: dict[str, Any]) -> None:  # pragma: no cover - replaced before play
    """The default contributor: a backend wired to no group cannot settle."""
    raise LocalDefectError("this backend was never given a group to contribute its rows to")


async def unreported(consensus_sha256: str) -> None:  # pragma: no cover - replaced before play
    """The default sink: a backend wired to no group cannot report a settlement."""
    raise LocalDefectError("this backend was never given a group to report its settlement to")


async def unavailable() -> tuple[dict[str, Any], ...]:  # pragma: no cover - replaced before play
    """The default reader: a backend wired to no group cannot see the series."""
    raise LocalDefectError("this backend was never given a way to read the group's series")


@dataclass(slots=True)
class SeriesSettler:
    """Everything the final settlement needs, kept out of the sub-game player.

    Split from `KitRoleBackend` because settling a series and playing a sub-game
    are different jobs that happen to end up in the same process: one owns turns,
    legality, scent and a chain; this one owns six finished rows and a digest.
    """

    send: "Callable[[dict[str, Any]], Awaitable[bool]]"
    received: "Callable[[], KitAuditReveal | None]"
    series_rows: "Callable[[], Awaitable[tuple[dict[str, Any], ...]]]"
    window: float
    retry: float

    async def settle(self, game_id: str, ours: str, theirs: str, our_role: str) -> str | None:
        """Agree the whole series with the peer, or report that it was not agreed."""
        digest = consensus_sha256(consensus_scope(game_id, await self.series_rows(), ours, theirs))
        exchange = SettlementExchange(
            send=self.send, received=self.received, window=self.window, retry=self.retry
        )
        return await exchange.settle(our_role, digest)


@dataclass(slots=True)
class BackendSettlement:
    """Everything a role backend needs to take part in settling its series.

    One field on the backend instead of five, because these values are only ever
    used together and none of them means anything to playing a sub-game: where
    finished rows go, where the assembled series comes back from, and the two
    numbers the pairing agreed for the exchange.
    """

    contribute: "Callable[[dict[str, Any]], Awaitable[None]]" = uncollected
    series_rows: "Callable[[], Awaitable[tuple[dict[str, Any], ...]]]" = unavailable
    window: float = field(default_factory=consensus_window)
    retry: float = field(default_factory=consensus_retry)
    agreed: str | None = None
    """The digest the series settled on, or `None` when it settled on nothing."""

    report_series: "Callable[[str], Awaitable[None]]" = field(default=unreported)
    """Where the agreed whole-series digest goes, so the group can render a result.

    Reported rather than rendered here: the result needs the merged declaration,
    which only the gateway holds. A backend rendering its own copy would give one
    file two authors."""

    async def settle(
        self,
        pairing: KitPairing,
        our_role: KitRole,
        send: "Callable[[dict[str, Any]], Awaitable[bool]]",
        received: "Callable[[], KitAuditReveal | None]",
    ) -> str | None:
        """Agree the whole series with the peer, or record that it was not agreed.

        A series the group could not assemble settles on nothing, and says so.
        That is not a swallowed error: six played sub-games are evidence worth
        keeping, and losing them because the settlement could not be *computed*
        would be a worse answer than recording honestly that none was reached.

        **But it still waits.** Returning early here is what broke a live g06:
        this side could not assemble six rows yet, returned instantly, `run()`
        finished, the held client closed and our inbound surface disappeared -
        while the peer was still sending g06's audit. It saw
        `PeerUnreachable: Session terminated`.

        Being unable to compute *our* digest is not permission to stop being
        reachable. The side that owns the final sub-game stays up for the whole
        agreed window either way; it simply has nothing of its own to send.

        **And it does not leave the moment the exchange succeeds.** rerun-9
        settled correctly and this process still refused two `submit_audit`
        calls that arrived one and three seconds after it had gone. Nothing was
        lost there, because both sides had already agreed the same digest - but
        rule 35 scores a series with no agreed result 0 for both groups, so
        being reachable when the peer is still talking is not something to leave
        to timing. The exchange and the wait that follows it share **one**
        deadline, so staying longer never costs more than the window both sides
        agreed.
        """
        deadline = asyncio.get_running_loop().time() + self.window
        if len(await self.series_rows()) != SUB_GAMES:
            self.agreed = None
            await self._wait_out(received, deadline)
            return None
        settler = SeriesSettler(
            send=send,
            received=received,
            series_rows=self.series_rows,
            window=self.window,
            retry=self.retry,
        )
        self.agreed = await settler.settle(
            pairing.game_id, pairing.our_group, pairing.peer_group, our_role.value
        )
        if self.agreed is not None:
            await self.report_series(self.agreed)
        await self._linger(received, deadline)
        return self.agreed

    def _remaining(self, deadline: float) -> float:
        """What is left of the one agreed window, never negative."""
        return max(0.0, deadline - asyncio.get_running_loop().time())

    async def _wait_out(
        self, received: "Callable[[], KitAuditReveal | None]", deadline: float
    ) -> None:
        """Stay reachable for the agreed window without sending a settlement.

        Receive-only: with no assembled series there is no digest of ours to
        offer, but the peer's audit and settlement still have to land somewhere.
        Ends on the first arrival, because that arrival is what it was waiting
        for; the post-exchange wait ends on silence instead.
        """
        while self._remaining(deadline) > 0 and received() is None:
            await asyncio.sleep(min(self.retry, self._remaining(deadline)))

    async def _linger(
        self, received: "Callable[[], KitAuditReveal | None]", deadline: float
    ) -> None:
        """Stay reachable after the exchange until the peer has gone quiet.

        Bounded twice, and the second bound is why a settled series still ends
        promptly: it stops as soon as the peer has sent nothing for
        `QUIET_RETRIES` of its own resend cadence, rather than always paying out
        the remainder of the window.
        """
        quiet = 0.0
        while self._remaining(deadline) > 0 and quiet < self.retry * QUIET_RETRIES:
            await asyncio.sleep(min(self.retry, self._remaining(deadline)))
            quiet = 0.0 if received() is not None else quiet + self.retry
