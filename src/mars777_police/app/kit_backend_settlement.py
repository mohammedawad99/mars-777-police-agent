"""What a role backend brings to settling the series it helped play.

Split from `kit_settlement` under guideline §3.2: that module owns *when* a
series settles and the exchange that settles it; this one owns what one backend
of a two-process group contributes to it. Neither has anything to say about
playing a sub-game.
"""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any

from ..domain.terminal import Outcome
from ..infra.game_contract import consensus_retry, consensus_window
from .kit_greeting import KitPairing
from .kit_messages import KitAuditReveal, KitRole
from .kit_schedule import SUB_GAMES
from .kit_settled_row import settled_row
from .kit_settlement import SettlementExchange
from .protocol_errors import LocalDefectError
from .series_consensus import consensus_scope, consensus_sha256


async def uncollected(row: dict[str, Any]) -> None:  # pragma: no cover - replaced before play
    """The default contributor: a backend wired to no group cannot settle."""
    raise LocalDefectError("this backend was never given a group to contribute its rows to")


async def unavailable() -> tuple[dict[str, Any], ...]:  # pragma: no cover - replaced before play
    """The default reader: a backend wired to no group cannot see the series."""
    raise LocalDefectError("this backend was never given a way to read the group's series")


def row_of(
    pairing: "KitPairing", sub_game: int, our_role: "KitRole", outcome: "Outcome"
) -> dict[str, Any]:
    """One finished sub-game as a settlement reads it, from the pairing's own names."""
    return settled_row(
        sub_game=sub_game,
        ours=pairing.our_group,
        theirs=pairing.peer_group,
        our_role=our_role,
        outcome=outcome,
    )


@dataclass(slots=True)
class SeriesSettler:
    """Everything the final settlement needs, kept out of the sub-game player.

    Split from `KitRoleBackend` because settling a series and playing a sub-game
    are different jobs that happen to end up in the same process: one owns turns,
    legality, scent and a chain; this one owns six finished rows and a digest.
    """

    send: "Callable[[dict[str, Any]], Awaitable[None]]"
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

    async def settle(
        self,
        pairing: KitPairing,
        our_role: KitRole,
        send: "Callable[[dict[str, Any]], Awaitable[None]]",
        received: "Callable[[], KitAuditReveal | None]",
    ) -> str | None:
        """Agree the whole series with the peer, or record that it was not agreed.

        A series the group could not assemble settles on nothing, and says so.
        That is not a swallowed error: six played sub-games are evidence worth
        keeping, and losing them because the settlement could not be *computed*
        would be a worse answer than recording honestly that none was reached.
        """
        if len(await self.series_rows()) != SUB_GAMES:
            self.agreed = None
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
        return self.agreed
