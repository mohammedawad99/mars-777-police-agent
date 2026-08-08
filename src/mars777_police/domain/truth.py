"""Local authoritative own truth.

``domain.truth`` is the single owner of this agent's **own** position, its
completed-step count and its own barrier budget (`STATE_OWNERSHIP.md`;
PRD01-FR-013, PRD01-FR-020). It is written only after validation, by the
application turn service.

It also carries the board, which holds the **public** barrier facts
(`STATE_OWNERSHIP.md` classifies the barrier set as PUBLIC) so an action can be
validated against real geometry. It is not a second authoritative copy of that
set: there is deliberately **no** local placement counter, because barriers
exist once, in `domain.barriers` / the board (`STATE_OWNERSHIP.md`
anti-duplication rule 2), and the quota is enforced against those facts. Any
remaining budget is therefore derived, never stored. It holds no data about the
other agent (PRD01-FR-021).

The own position must stay **in bounds** but need not stay traversable: BAR-004
lets the police place a barrier on its own cell, after which the agent legally
stands on a blocked cell.
"""

from dataclasses import dataclass

from .board import Board, Position
from .errors import DomainError, require_int


class InvalidTruthError(DomainError):
    """Raised when local own-truth values are malformed or out of bounds."""


@dataclass(frozen=True, slots=True)
class LocalTruth:
    """This agent's own authoritative state for one sub-game."""

    board: Board
    own_position: Position
    completed_steps: int = 0

    def __post_init__(self) -> None:
        if not isinstance(self.board, Board):
            raise InvalidTruthError(f"board must be a Board, got {type(self.board).__name__}")
        if not isinstance(self.own_position, Position):
            raise InvalidTruthError(
                f"own_position must be a Position, got {type(self.own_position).__name__}",
            )
        if not self.board.contains(self.own_position):
            raise InvalidTruthError(
                f"own_position [{self.own_position.row},{self.own_position.col}]"
                " lies outside the board",
            )
        require_int(self.completed_steps, "completed_steps", InvalidTruthError)
        if self.completed_steps < 0:
            raise InvalidTruthError(
                f"completed_steps must be >= 0, got {self.completed_steps}",
            )
