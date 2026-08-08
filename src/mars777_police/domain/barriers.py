"""Deterministic barrier-placement semantics.

BAR-004 (PDF p.37): on a turn the police forgoes movement it may place a
barrier on its own cell or on one orthogonally-adjacent cell; that cell becomes
impassable to both players, irreversibly, until the end of the game.
BAR-005 / App F T15 #2: the quota is configured, MINIMUM 14.

Scope boundaries:

* This module decides whether a *declared* placement satisfies the rulebook.
  It is not an authorisation control: the domain cannot know which process is
  the police. Both repositories run this identical verification against the
  openly declared placement (BAR-001/BAR-002).
* ``place_barrier`` returns a new ``Board`` and nothing else, so the effect is
  structurally incapable of also moving the actor. Enforcing "move OR place in
  one turn" is turn orchestration and belongs to a later stage (PRD-02).
* Removal and relocation are not expressible: no API mutates or clears a
  barrier (PRD01-FR-033 irreversibility).
"""

from dataclasses import dataclass
from typing import Final

from .board import ORTHOGONAL_OFFSETS, Board, Position
from .errors import DomainError, require_int

MIN_MAX_BARRIERS: Final[int] = 14
"""Locked floor for the barrier quota (App F T15 #2, MINIMUM; BAR-005)."""


class InvalidBarrierError(DomainError):
    """Raised when a barrier quota or a barrier placement is invalid."""


@dataclass(frozen=True, slots=True)
class BarrierQuota:
    """The configured maximum number of barriers (BAR-005)."""

    max_barriers: int

    def __post_init__(self) -> None:
        require_int(self.max_barriers, "max_barriers", InvalidBarrierError)
        if self.max_barriers < MIN_MAX_BARRIERS:
            raise InvalidBarrierError(
                f"max_barriers must be >= {MIN_MAX_BARRIERS}, got {self.max_barriers}",
            )


def is_adjacent_or_same(actor: Position, target: Position) -> bool:
    """Return True when *target* is the actor's cell or a cardinal neighbour."""
    if not isinstance(actor, Position) or not isinstance(target, Position):
        return False
    if actor == target:
        return True
    offset = (target.row - actor.row, target.col - actor.col)
    return offset in ORTHOGONAL_OFFSETS


def is_placeable(board: Board, actor: Position, target: Position, quota: BarrierQuota) -> bool:
    """Return True when placing a barrier on *target* satisfies BAR-004/BAR-005.

    A verdict, never an exception: the value is a position, the target is the
    actor's own or a cardinally adjacent cell, it is inside the board, it is
    not already blocked, and the quota still has room.
    """
    if not isinstance(board, Board) or not isinstance(quota, BarrierQuota):
        return False
    if not is_adjacent_or_same(actor, target):
        return False
    if not board.contains(target) or board.is_blocked(target):
        return False
    return len(board.blocked) < quota.max_barriers


def place_barrier(
    board: Board,
    actor: Position,
    target: Position,
    quota: BarrierQuota,
) -> Board:
    """Return a new board carrying the added barrier.

    Neither *board* nor *actor* is mutated, and the actor's position is not
    part of the result: a placement can never move the agent that made it.
    An invalid placement raises before any new board exists.
    """
    if not is_placeable(board, actor, target, quota):
        raise InvalidBarrierError(f"illegal barrier placement at {_cell(target)}")
    return Board(
        rows=board.rows,
        cols=board.cols,
        start_index=board.start_index,
        blocked=board.blocked | {target},
    )


def _cell(position: object) -> str:
    if isinstance(position, Position):
        return f"[{position.row},{position.col}]"
    return f"<{type(position).__name__}>"
