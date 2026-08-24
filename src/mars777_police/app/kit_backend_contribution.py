"""What one role backend owns and its opponent cannot derive.

A settled row carries the scores and the outcome, which both peers compute from
the played sub-game and the locked scoring table. Two facts per sub-game are not
like that: the commit this backend played from, and the tokens it spent. They are
**participant-owned**, they travel in this participant's own `ResultContribution`,
and nobody else can supply them.

Kept as one value beside the settlement rather than as loose fields, so a backend
that plays a sub-game publishes both halves through one call and neither can be
forgotten.

**A token count is reported because the accounting authority answered.** It is
never inferred from an absent field, and there is no default standing in for a
measurement.
"""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field

from .kit_messages import KitRole
from .protocol_errors import LocalDefectError
from .token_accounting import SeriesTokenLedger, TokenAccountingPort


async def unentered(  # pragma: no cover - replaced before play
    sub_game: int, role: str, github_commit: str, tokens: int
) -> None:
    """The default sink: a backend wired to no group cannot contribute."""
    raise LocalDefectError("this backend was never given a group to contribute its entries to")


@dataclass(slots=True)
class BackendContribution:
    """This backend's participant-owned half of every sub-game it plays."""

    played_commit: str = field(default="")
    """The commit this repository declared for the role it plays, from Step-0."""

    tokens: TokenAccountingPort = field(default_factory=SeriesTokenLedger)
    """This side's token authority. A count is reported because this answered."""

    send: Callable[[int, str, str, int], Awaitable[None]] = unentered
    """How the entry reaches the group, injected by composition."""

    async def publish(self, sub_game: int, role: KitRole) -> None:
        """Hand the group this backend's own entry for a sub-game it just played."""
        await self.send(sub_game, role.value, self.played_commit, self.tokens.usage(sub_game))
