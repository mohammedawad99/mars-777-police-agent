"""Deterministic, role-neutral game domain (Stage 3A foundation).

Pure value objects and pure functions only: no I/O, no network, no clock, no
filesystem, no global mutable state and no randomness (PRD01-NFR-001). The
domain imports nothing from the application, protocol or infrastructure
layers (``docs/architecture/DEPENDENCY_RULES.md`` rule D1).

Stage 3A provides the primitives that later game semantics need: grid
configuration, coordinates, the board and blocked cells, the five-token move
set, movement legality, legal-move enumeration and safe move application.
Barriers as an action, capture, scoring, scent, belief, observation and
strategy are **not** implemented here.

No type in this package carries opponent truth (PRD01-FR-021).
"""

from .board import Board, InvalidBoardError, Position
from .config_model import MIN_GRID_SIZE, GridConfig, InvalidGridConfigError
from .errors import DomainError
from .rules import (
    MOVE_ORDER,
    IllegalMoveError,
    Move,
    apply_move,
    delta_of,
    destination_of,
    is_legal_move,
    legal_moves,
)

__all__ = [
    "MIN_GRID_SIZE",
    "MOVE_ORDER",
    "Board",
    "DomainError",
    "GridConfig",
    "IllegalMoveError",
    "InvalidBoardError",
    "InvalidGridConfigError",
    "Move",
    "Position",
    "apply_move",
    "delta_of",
    "destination_of",
    "is_legal_move",
    "legal_moves",
]
