"""The one authoritative physical action a turn consists of.

Ch 5 §5.3.1 (p.51) defines the sealed ``Move`` as *"the physical action; the
chosen action (movement, **barrier placement**, etc.)"* - *"the core that is to
be locked against change"*. That action is a **game-domain** value: PRD-01 owns
the legal action space, it exists before any transport, and it is the same value
local execution applies, the future ``protocol.commitment`` seals under the
sealed record's ``move`` member, and Reveal exposes. It therefore lives here,
where ``app.turn_service``, ``app.peer_messages`` and ``protocol.commitment`` can
all reach it while this module reaches none of them (Stage 4E-R4).

Ch 3 §3.4 (p.37) gives the two forms: a turn is **one single action** - move one
orthogonal cell **or stay** - and the police may place a barrier only *"in a turn
in which he forgoes movement"*, declaring **its exact location** truthfully. So
the two forms are structurally exclusive, ``Move.STAY`` is an ordinary movement
rather than a null action, and a barrier binds its exact cell.

Validation here is **structural only**: exact composed types and no coercion.
Everything that needs context - actor role, the thief's barrier prohibition,
board bounds, the within-one-step rule, occupancy, quota, current position, phase
and locked config - is LIVE and stays in the rules and the turn service. A value
that needed a ``Board`` to be constructed would not be a value.

The canonical JSON shape of this action is frozen in
`CANONICALIZATION_CONTRACT.md` and NDEC-001, but **nothing here serializes**: no
encoding, no digest, no wire form. That is a later protocol slice.
"""

from dataclasses import dataclass
from enum import StrEnum

from .board import Position
from .errors import DomainError
from .rules import Move


class InvalidPhysicalActionError(DomainError):
    """Raised when a physical action is composed from a malformed value."""


class ActionKind(StrEnum):
    """The kinds of physical action a turn may consist of."""

    MOVE = "MOVE"
    BARRIER = "BARRIER"


@dataclass(frozen=True, slots=True)
class MoveAction:
    """Move exactly one cell, or STAY. Carries no placement target.

    ``move`` must already be a ``Move``: a raw ``"N"`` is refused rather than
    parsed, so the movement vocabulary keeps one authoritative form and a caller
    can always tell which contract validated it. Turning a wire token into a
    ``Move`` is the protocol layer's job - the domain never guesses.
    """

    move: Move

    def __post_init__(self) -> None:
        if type(self.move) is not Move:
            raise InvalidPhysicalActionError(
                f"move must be a Move, got {type(self.move).__name__}",
            )

    @property
    def kind(self) -> ActionKind:
        """Return this action's kind."""
        return ActionKind.MOVE


@dataclass(frozen=True, slots=True)
class BarrierAction:
    """Place a barrier on one exact cell. Carries no move.

    The cell is the action's structural identity - Ch 3 p.37/38 require every
    placement **and its exact location** to be declared truthfully - so it is
    never derived from the actor's position, a direction or later context.
    Whether that cell is *legal* is LIVE and belongs to ``domain.barriers``.
    """

    target: Position

    def __post_init__(self) -> None:
        if type(self.target) is not Position:
            raise InvalidPhysicalActionError(
                f"target must be a Position, got {type(self.target).__name__}",
            )

    @property
    def kind(self) -> ActionKind:
        """Return this action's kind."""
        return ActionKind.BARRIER


PhysicalAction = MoveAction | BarrierAction
"""The chosen physical action: exactly one movement **or** one placement.

A union rather than a base class: the two forms share no behaviour worth
inheriting, and an exclusive union makes "one action per turn" structural
instead of a rule someone has to remember to check.
"""
