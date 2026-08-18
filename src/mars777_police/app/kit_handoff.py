"""Which sub-game is live, which backend owns it, and when the next may start.

The pinned peer greets for the next sub-game the moment it has settled the
previous one, so a greeting for `n+1` legitimately arrives while `n` is still
draining its audit exchange. Acknowledging that greeting into a queue nobody
drains is the hazard the kit's own documentation names: the opponent burns its
whole connect budget on a message we answered `ok` and never acted on.

Three explicit states rather than a boolean, because the middle one is real:

* `ACTIVE(n)` - turns for `n` route to the backend playing `n`;
* `SETTLING(n)` - `n` reached its end event and its audits are still moving, so
  gameplay must not move on yet;
* `READY(n)` - `n` is finished and `n+1` may be assigned.

**Settlement is signalled, never inferred.** HTTP silence means nothing here: a
peer that is thinking looks exactly like a peer that has finished, and guessing
between them is how a sub-game gets skipped. The backend that played `n` says so.

This owns no board, no position, no rule and no score. It owns which backend the
next message belongs to, and that is all.
"""

import asyncio
from dataclasses import dataclass, field
from enum import StrEnum

from .kit_messages import KitRole
from .kit_schedule import SUB_GAMES, role_for
from .protocol_errors import StaleMessageError


class HandoffPhase(StrEnum):
    """Where one sub-game stands, from the routing layer's point of view."""

    ACTIVE = "ACTIVE"
    """Its turns are live and route to the backend playing it."""

    SETTLING = "SETTLING"
    """It reached an end event; its audit exchange has not finished."""

    READY = "READY"
    """It is finished. The next sub-game may be assigned."""


@dataclass(slots=True)
class SeriesHandoff:
    """One series' cursor across two role backends, and the gate between them."""

    first_role: KitRole
    sub_game: int = 1
    phase: HandoffPhase = HandoffPhase.ACTIVE
    released: asyncio.Event = field(default_factory=asyncio.Event)

    @property
    def role(self) -> KitRole:
        """The side we take in the live sub-game, from the frozen schedule."""
        return role_for(self.first_role, self.sub_game)

    def role_of(self, sub_game: int) -> KitRole:
        """The side the schedule gives *sub_game*, whether or not it is live."""
        return role_for(self.first_role, sub_game)

    def begin_settlement(self) -> None:
        """`ACTIVE(n)` -> `SETTLING(n)`: an end event was reached."""
        self.phase = HandoffPhase.SETTLING

    def settled(self) -> None:
        """`SETTLING(n)` -> `READY(n)`: the backend says it owes nothing more."""
        self.phase = HandoffPhase.READY
        self.released.set()

    def assignable(self, sub_game: int) -> bool:
        """Whether a greeting for *sub_game* can be handed to a backend now."""
        if sub_game == self.sub_game:
            return True
        return sub_game == self.sub_game + 1 and self.phase is HandoffPhase.READY

    async def await_assignable(self, sub_game: int, timeout: float) -> None:
        """Hold a next-sub-game greeting until it is safe to assign, or give up.

        Bounded, and it never acknowledges on its own: the caller acknowledges
        only after this returns, which is what makes an `ok` mean "assigned".
        """
        while not self.assignable(sub_game):
            self.released.clear()
            await asyncio.wait_for(self.released.wait(), timeout)

    def open(self, sub_game: int) -> None:
        """Make *sub_game* the live one, or refuse a cursor that cannot be next."""
        if sub_game == self.sub_game:
            return
        if not self.assignable(sub_game):
            raise StaleMessageError(
                f"sub-game {sub_game} cannot open while {self.sub_game} is"
                f" {self.phase.value}; one series advances one sub-game at a time",
            )
        if sub_game > SUB_GAMES:
            raise StaleMessageError(f"a series is {SUB_GAMES} sub-games; {sub_game} is past it")
        self.sub_game, self.phase = sub_game, HandoffPhase.ACTIVE
        self.released.clear()
