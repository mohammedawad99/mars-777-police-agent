"""Deterministic, role-neutral game domain (Stage 3A foundation).

Pure value objects and pure functions only: no I/O, no network, no clock, no
filesystem, no global mutable state and no randomness (PRD01-NFR-001). The
domain imports nothing from the application, protocol or infrastructure
layers (``docs/architecture/DEPENDENCY_RULES.md`` rule D1).

Stage 3A provided the primitives: grid configuration, coordinates, the board
and blocked cells, the five-token move set, movement legality, legal-move
enumeration and safe move application. Stage 3B adds the remaining PRD-01
semantics: barrier placement, the three capture routes, terminal/survival
evaluation, role-keyed scoring and scent physics, and Stage 4C the FIXED
counted-series length. Belief, observation, strategy, orchestration, protocol
and reporting are **not** implemented here.

No type in this package carries opponent truth (PRD01-FR-021).
"""

from .barriers import (
    MIN_MAX_BARRIERS,
    BarrierQuota,
    InvalidBarrierError,
    is_adjacent_or_same,
    is_placeable,
    place_barrier,
)
from .board import ORTHOGONAL_OFFSETS, Board, InvalidBoardError, Position
from .config_model import (
    FIRST_SUB_GAME,
    FIXED_CENTER_INTENSITY,
    FIXED_DECAY,
    FIXED_FIELD_SIZE,
    FIXED_NUM_GAMES,
    MIN_GRID_SIZE,
    GridConfig,
    InvalidGridConfigError,
    InvalidScentError,
    InvalidSeriesError,
    ScentParams,
    SeriesConfig,
)
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
from .scent import MAX_SCENT_STATE, ScentField
from .scent_kernel import ScentKernel
from .scoring import (
    CAPTURE_SCORE,
    SURVIVAL_SCORE,
    TECHNICAL_LOSS_SCORE,
    TIE_SCORE,
    ScoreLine,
    score_for,
)
from .terminal import (
    MIN_MAX_MOVES,
    MIN_SURVIVAL_THRESHOLD,
    InvalidTurnLimitsError,
    Outcome,
    TurnLimits,
    evaluate_terminal,
    is_barrier_capture,
    is_same_cell,
    is_trapped,
)

__all__ = [
    "CAPTURE_SCORE",
    "FIRST_SUB_GAME",
    "FIXED_CENTER_INTENSITY",
    "FIXED_DECAY",
    "FIXED_FIELD_SIZE",
    "FIXED_NUM_GAMES",
    "MAX_SCENT_STATE",
    "MIN_GRID_SIZE",
    "MIN_MAX_BARRIERS",
    "MIN_MAX_MOVES",
    "MIN_SURVIVAL_THRESHOLD",
    "MOVE_ORDER",
    "ORTHOGONAL_OFFSETS",
    "SURVIVAL_SCORE",
    "TECHNICAL_LOSS_SCORE",
    "TIE_SCORE",
    "BarrierQuota",
    "Board",
    "DomainError",
    "GridConfig",
    "IllegalMoveError",
    "InvalidBarrierError",
    "InvalidBoardError",
    "InvalidGridConfigError",
    "InvalidScentError",
    "InvalidSeriesError",
    "InvalidTurnLimitsError",
    "Move",
    "Outcome",
    "Position",
    "ScentField",
    "ScentKernel",
    "ScentParams",
    "ScoreLine",
    "SeriesConfig",
    "TurnLimits",
    "apply_move",
    "delta_of",
    "destination_of",
    "evaluate_terminal",
    "is_adjacent_or_same",
    "is_barrier_capture",
    "is_legal_move",
    "is_placeable",
    "is_same_cell",
    "is_trapped",
    "legal_moves",
    "place_barrier",
    "score_for",
]
