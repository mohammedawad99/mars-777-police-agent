"""Deterministic movement vocabulary and movement legality.

Scope (Stage 3A): the five-token move set, its exact deltas, a stable
enumeration order, and whether a proposed move's destination is usable. It
deliberately contains **no** capture, scoring, barrier-placement or scent
semantics -- those are later stages.

Legality is reported as a verdict and never raises (PRD-01 §17):
``is_legal_move`` and ``legal_moves`` are total. ``apply_move`` is the effect
operation; calling it with a move the verdict API already rejects is a caller
defect and fails fast with a typed error, leaving every input untouched
(PRD01-FR-011, PRD01-FR-012).

Axis convention: the locked default ``axis_origin_corner`` is ``"top-left"``
with the row index growing downward, so N decreases the row. A non-default
origin corner is NEGOTIABLE and is not implemented in Stage 3A.
"""

from enum import StrEnum
from typing import Final

from .board import Board, Position
from .errors import DomainError


class IllegalMoveError(DomainError):
    """Raised when an effect is requested for a move that is not legal."""


class Move(StrEnum):
    """The locked action alphabet ``move_set`` (PRD01-FR-003, FIXED)."""

    N = "N"
    S = "S"
    E = "E"
    W = "W"
    STAY = "STAY"


MOVE_ORDER: Final[tuple[Move, ...]] = (Move.N, Move.S, Move.E, Move.W, Move.STAY)
"""Stable enumeration order.

Project-deterministic behaviour matching the source listing order, **not** an
additional book numeric rule. Enumeration never iterates a set or a dict, so
results cannot depend on Python hash randomization (PRD-01 §19).
"""

_DELTAS: Final[dict[Move, tuple[int, int]]] = {
    Move.N: (-1, 0),
    Move.S: (1, 0),
    Move.E: (0, 1),
    Move.W: (0, -1),
    Move.STAY: (0, 0),
}


def delta_of(move: Move) -> tuple[int, int]:
    """Return the exact ``(d_row, d_col)`` of *move*.

    Every non-STAY delta changes exactly one axis by exactly one cell, so no
    diagonal and no multi-cell move is representable (PRD01-FR-004, GAME-004).
    """
    if not isinstance(move, Move):
        raise IllegalMoveError(f"unknown move token of type {type(move).__name__}")
    return _DELTAS[move]


def destination_of(position: Position, move: Move) -> Position:
    """Return the cell *move* leads to from *position*, without validating it."""
    if not isinstance(position, Position):
        raise IllegalMoveError(f"position must be a Position, got {type(position).__name__}")
    d_row, d_col = delta_of(move)
    return Position(position.row + d_row, position.col + d_col)


def is_legal_move(board: Board, position: Position, move: Move) -> bool:
    """Return True when *move* from *position* lands on a usable cell.

    Stage-3A legality is exactly: the value is one of the five moves, the
    destination is inside the board, and the destination is not blocked. STAY
    resolves to the current cell and is judged by the same mechanism.

    Only a real ``Move`` is accepted. ``Move`` is a ``StrEnum``, so ``"N"``
    *compares* equal to ``Move.N``, but parsing a wire token into a ``Move``
    is the protocol layer's job -- the domain never guesses.
    """
    if not isinstance(board, Board) or not isinstance(position, Position):
        return False
    if not isinstance(move, Move):
        return False
    return board.is_traversable(destination_of(position, move))


def legal_moves(board: Board, position: Position) -> tuple[Move, ...]:
    """Return every legal move from *position* in the stable project order."""
    return tuple(move for move in MOVE_ORDER if is_legal_move(board, position, move))


def apply_move(board: Board, position: Position, move: Move) -> Position:
    """Return the position reached by a legal *move*.

    Neither *board* nor *position* is mutated: both are frozen value objects
    and a new ``Position`` is returned. An illegal move raises before any
    result exists, so no partial state can be produced.
    """
    if not is_legal_move(board, position, move):
        raise IllegalMoveError(f"illegal move {_token(move)} from {_cell(position)}")
    return destination_of(position, move)


def _token(move: object) -> str:
    return move.value if isinstance(move, Move) else f"<{type(move).__name__}>"


def _cell(position: object) -> str:
    if isinstance(position, Position):
        return f"[{position.row},{position.col}]"
    return f"<{type(position).__name__}>"
