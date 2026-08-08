"""Capture routes and terminal / survival evaluation.

This is the ``domain.rules`` responsibility "capture, terminal conditions",
split into its own file to honour the <=150-line rule; PRD-01 §27 leaves that
exact split open as an implementation decision. Same layer, same inward
dependency direction, no new responsibility.

Locked sources:

* PDF p.37 (GAME-005): a thief trapped "without any legal move (**all adjacent
  cells** blocked by barriers and/or the board edge)" is likewise captured.
  The parenthetical defines the rule over *adjacent cells*, so STAY - a legal
  Stage-3A move - is not an escape and does not prevent this capture.
* BAR-003: a barrier placed on the thief's current cell is a capture.
* Ch 3 Table 2: exactly three sub-game end events - successful capture,
  prolonged survival ("the thief survives [survival_threshold] valid steps
  **without capture**") and technical loss. That wording is the locked
  precedence: capture is decided before any step threshold.
* GAME-008 / App F T15 #3,#4: the step ceiling and the survival threshold come
  from configuration, both MINIMUM 35, never hard-coded. The source lets the
  two be raised independently but defines **no** outcome for a survival
  threshold the step ceiling can never reach, so **JDEC-015** (PROJECT-CONTRACT)
  makes ``survival_threshold <= max_moves`` an admissibility condition: such a
  configuration is refused rather than given an invented terminal. The refusal
  belongs to config validation once ``CONFIG_LOCKED`` exists; this guard only
  keeps an inadmissible ``TurnLimits`` from being constructed at all.

Technical loss (crash, timeout, cryptographic forgery) is a protocol-layer
fact; the domain owns only its scoring key, not its detection.

No function here stores state, and no type pairs the two agents' true
positions: the predicates take the minimum cells needed and retain nothing.
"""

from dataclasses import dataclass
from enum import StrEnum
from typing import Final

from .board import Board, Position
from .errors import DomainError, require_int

MIN_MAX_MOVES: Final[int] = 35
MIN_SURVIVAL_THRESHOLD: Final[int] = 35


class InvalidTurnLimitsError(DomainError):
    """Raised when configured step limits violate the locked minimums."""


class Outcome(StrEnum):
    """The locked sub-game end events (Ch 3 Table 2).

    There is deliberately no TIE member: App F T17 #5 scopes ``tie_score`` to a
    tied **cumulative** score against an opponent, which is a series-level
    concern, and Table 2 has no tie row.
    """

    CAPTURE = "CAPTURE"
    SURVIVAL = "SURVIVAL"
    TECHNICAL_LOSS = "TECHNICAL_LOSS"


@dataclass(frozen=True, slots=True)
class TurnLimits:
    """Configured step ceiling and survival threshold (GAME-008)."""

    max_moves: int
    survival_threshold: int

    def __post_init__(self) -> None:
        require_int(self.max_moves, "max_moves", InvalidTurnLimitsError)
        require_int(self.survival_threshold, "survival_threshold", InvalidTurnLimitsError)
        if self.max_moves < MIN_MAX_MOVES:
            raise InvalidTurnLimitsError(
                f"max_moves must be >= {MIN_MAX_MOVES}, got {self.max_moves}",
            )
        if self.survival_threshold < MIN_SURVIVAL_THRESHOLD:
            raise InvalidTurnLimitsError(
                f"survival_threshold must be >= {MIN_SURVIVAL_THRESHOLD},"
                f" got {self.survival_threshold}",
            )
        if self.survival_threshold > self.max_moves:
            raise InvalidTurnLimitsError(
                f"survival_threshold {self.survival_threshold} exceeds max_moves"
                f" {self.max_moves}: unreachable threshold (JDEC-015)",
            )


def is_same_cell(one: Position, other: Position) -> bool:
    """Return True when two cells are identical (PRD01-FR-050 contact capture).

    A stateless comparison of two cells supplied by the caller.
    """
    if not isinstance(one, Position) or not isinstance(other, Position):
        return False
    return one == other


def is_barrier_capture(target: Position, occupied: Position) -> bool:
    """Return True when a barrier lands on the occupied cell (BAR-003)."""
    return is_same_cell(target, occupied)


def is_trapped(board: Board, position: Position) -> bool:
    """Return True when every adjacent cell is blocked or off the board.

    GAME-005 as the source defines it: the board edge counts exactly like a
    barrier, diagonals are not adjacencies, and STAY is irrelevant here.
    """
    if not isinstance(board, Board) or not isinstance(position, Position):
        return False
    return not any(
        board.is_traversable(neighbour) for neighbour in board.orthogonal_neighbours(position)
    )


def evaluate_terminal(*, captured: bool, step: int, limits: TurnLimits) -> Outcome | None:
    """Return the sub-game outcome, or None while play continues.

    Precedence is the locked one: capture first (Table 2 makes survival
    conditional on *no capture*), then the configured survival threshold. A
    step outside ``[0, max_moves]`` is invalid input, never an outcome.

    Admissible limits guarantee ``survival_threshold <= max_moves``
    (JDEC-015), so every step inside the ceiling resolves deterministically.
    """
    if not isinstance(limits, TurnLimits):
        raise InvalidTurnLimitsError("limits must be TurnLimits")
    require_int(step, "step", InvalidTurnLimitsError)
    if step < 0:
        raise InvalidTurnLimitsError(f"step must be >= 0, got {step}")
    if step > limits.max_moves:
        raise InvalidTurnLimitsError(
            f"step {step} exceeds max_moves {limits.max_moves}",
        )
    if captured:
        return Outcome.CAPTURE
    if step >= limits.survival_threshold:
        return Outcome.SURVIVAL
    return None
