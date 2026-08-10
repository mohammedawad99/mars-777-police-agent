"""The four board-side Appendix-B config sections as typed value objects.

``domain.config_model`` already owns the grid, series and pheromone primitives
and is at its line budget, so the remaining sections live here and in
``domain.config_league_sections`` (`MODULE_BOUNDARIES.md`, Stage 4E-R14-R1).

Each value validates **one proposed config** against its frozen Appendix-F
status: FIXED values must match exactly, MINIMUM values may only rise. Opponent
equality, negotiation cadence and the current sub-game are LIVE concerns and
appear nowhere here.
"""

from dataclasses import dataclass
from typing import Final

from .board import Position
from .config_model import MIN_GRID_SIZE, GridConfig
from .errors import DomainError, require_int

FIXED_NUM_AGENTS: Final[int] = 2
FIXED_MOVE_SET: Final[tuple[str, ...]] = ("N", "S", "E", "W", "STAY")
MIN_MAX_BARRIERS: Final[int] = 14
MIN_MAX_MOVES: Final[int] = 35
MIN_SURVIVAL_THRESHOLD: Final[int] = 35
FIXED_SCORES: Final[tuple[tuple[str, int], ...]] = (
    ("capture_cop", 20),
    ("capture_thief", 5),
    ("survival_cop", 5),
    ("survival_thief", 10),
    ("tie_score", 2),
    ("technical_loss", 0),
)
"""App F T17, plus ``technical_loss`` whose 0/0 provenance is Ch 3 Table 2 and
App E #48 - a binding key that is deliberately **not** an Appendix-F row (C-07).
"""


class InvalidConfigSectionError(DomainError):
    """Raised when a proposed config section violates its locked policy."""


def require_at_least(value: object, name: str, floor: int) -> int:
    number = require_int(value, name, InvalidConfigSectionError)
    if number < floor:
        raise InvalidConfigSectionError(f"{name} must be >= {floor}, got {number}")
    return number


@dataclass(frozen=True, slots=True)
class BoardAndAgentsTerms:
    """App F Table 13: geometry, agent count and the two start cells."""

    grid_size: int
    num_agents: int
    thief_start: Position
    cop_start: Position
    axis_origin_corner: str
    axis_start_index: int

    def __post_init__(self) -> None:
        require_at_least(self.grid_size, "grid_size", MIN_GRID_SIZE)
        require_int(self.num_agents, "num_agents", InvalidConfigSectionError)
        if self.num_agents != FIXED_NUM_AGENTS:
            raise InvalidConfigSectionError(
                f"num_agents is FIXED at {FIXED_NUM_AGENTS}, got {self.num_agents}",
            )
        if type(self.axis_origin_corner) is not str or not self.axis_origin_corner:
            raise InvalidConfigSectionError("axis_origin_corner must be a non-empty str")
        require_at_least(self.axis_start_index, "axis_start_index", 0)
        grid = GridConfig(self.grid_size, self.grid_size, self.axis_start_index)
        for name, cell in (("thief_start", self.thief_start), ("cop_start", self.cop_start)):
            if type(cell) is not Position:
                raise InvalidConfigSectionError(
                    f"{name} must be a Position, got {type(cell).__name__}",
                )
            low = grid.start_index
            high = low + self.grid_size - 1
            if not (low <= cell.row <= high and low <= cell.col <= high):
                raise InvalidConfigSectionError(f"{name} {cell} is outside the declared board")
        if self.thief_start == self.cop_start:
            raise InvalidConfigSectionError("thief_start and cop_start must differ")


@dataclass(frozen=True, slots=True)
class WorldTerms:
    """App F Table 14: the map label and the hint word budget."""

    map_area: str
    hint_max_words: int

    def __post_init__(self) -> None:
        if type(self.map_area) is not str:
            raise InvalidConfigSectionError(
                f"map_area must be a str, got {type(self.map_area).__name__}",
            )
        require_at_least(self.hint_max_words, "hint_max_words", 1)


@dataclass(frozen=True, slots=True)
class MovementAndBarrierTerms:
    """App F Table 15: the move vocabulary, barrier quota and turn limits."""

    move_set: tuple[str, ...]
    max_barriers: int
    max_moves: int
    survival_threshold: int

    def __post_init__(self) -> None:
        if type(self.move_set) is not tuple:
            raise InvalidConfigSectionError(
                f"move_set must be a tuple, got {type(self.move_set).__name__}",
            )
        if self.move_set != FIXED_MOVE_SET:
            raise InvalidConfigSectionError(
                f"move_set is FIXED at {FIXED_MOVE_SET}, got {self.move_set}",
            )
        require_at_least(self.max_barriers, "max_barriers", MIN_MAX_BARRIERS)
        require_at_least(self.max_moves, "max_moves", MIN_MAX_MOVES)
        require_at_least(self.survival_threshold, "survival_threshold", MIN_SURVIVAL_THRESHOLD)
        if self.survival_threshold > self.max_moves:
            raise InvalidConfigSectionError(
                "survival_threshold must be <= max_moves (JDEC-015), got"
                f" {self.survival_threshold} > {self.max_moves}",
            )


@dataclass(frozen=True, slots=True)
class ScoringTerms:
    """App F Table 17 plus the Ch 3 / App E #48 technical loss (C-07)."""

    capture_cop: int
    capture_thief: int
    survival_cop: int
    survival_thief: int
    tie_score: int
    technical_loss: int

    def __post_init__(self) -> None:
        for name, locked in FIXED_SCORES:
            value = require_int(getattr(self, name), name, InvalidConfigSectionError)
            if value != locked:
                raise InvalidConfigSectionError(f"{name} is FIXED at {locked}, got {value}")
