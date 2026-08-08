"""Immutable configuration value objects and their Appendix-F policy.

Stage 3A implements only the grid part of the locked configuration: the board
is a **square** grid whose size comes from ``board_and_agents.grid_size`` and
which MUST be rejected below 7 (PRD01-FR-001; App F T13 grid_size MINIMUM 7;
conflict C-01). ``MIN_GRID_SIZE`` is a validation floor, not a substitute for
the signed value -- the size itself is always supplied by the caller.

``axis_start_index`` is NEGOTIABLE with default 0 (PRD01-FR-002), so it is
carried here rather than hard-coded into the geometry.

Stage 3B adds the three **FIXED** pheromone parameters (App F Table 16:
centre 0.9, decay 0.10, field 5x5). They live here because this module owns the
typed view of the signed config and its FIXED/MINIMUM/NEGOTIABLE semantics; the
physics that consumes them lives in ``domain.scent``.

This module performs no I/O: it reads no file and no environment variable.
"""

from collections.abc import Iterable
from dataclasses import dataclass
from decimal import Decimal
from typing import Final

from .board import Board, Position
from .errors import DomainError, require_int

MIN_GRID_SIZE: Final[int] = 7
"""Locked project minimum for either grid axis (App F T13, MINIMUM; C-01)."""


class InvalidGridConfigError(DomainError):
    """Raised when declared grid geometry violates the locked policy."""


@dataclass(frozen=True, slots=True)
class GridConfig:
    """Immutable, validated grid geometry taken from the locked config."""

    rows: int
    cols: int
    start_index: int = 0

    def __post_init__(self) -> None:
        require_int(self.rows, "rows", InvalidGridConfigError)
        require_int(self.cols, "cols", InvalidGridConfigError)
        require_int(self.start_index, "start_index", InvalidGridConfigError)
        for name, extent in (("rows", self.rows), ("cols", self.cols)):
            if extent < MIN_GRID_SIZE:
                raise InvalidGridConfigError(
                    f"{name} must be >= {MIN_GRID_SIZE}, got {extent}",
                )
        if self.rows != self.cols:
            raise InvalidGridConfigError(
                f"grid must be square, got {self.rows}x{self.cols}",
            )
        if self.start_index < 0:
            raise InvalidGridConfigError(
                f"start_index must be >= 0, got {self.start_index}",
            )

    @classmethod
    def from_grid_size(cls, grid_size: int, start_index: int = 0) -> "GridConfig":
        """Build a square configuration from the config's single ``grid_size``."""
        return cls(rows=grid_size, cols=grid_size, start_index=start_index)

    def to_board(self, blocked: Iterable[Position] = ()) -> Board:
        """Build the geometry this configuration describes."""
        return Board(
            rows=self.rows,
            cols=self.cols,
            start_index=self.start_index,
            blocked=frozenset(blocked),
        )


FIXED_CENTER_INTENSITY: Final[Decimal] = Decimal("0.9")
"""App F T16 #1, FIXED: pheromone intensity deposited on the emitting cell."""

FIXED_DECAY: Final[Decimal] = Decimal("0.10")
"""App F T16 #2, FIXED: rho, the per-turn decay rate."""

FIXED_FIELD_SIZE: Final[int] = 5
"""App F T16 #3, FIXED: side of the square emission window."""


class InvalidScentError(DomainError):
    """Raised for invalid scent parameters, kernels, fields or cells."""


def require_decimal(value: object, name: str, *, allow_str: bool = False) -> Decimal:
    """Return *value* as a finite Decimal, rejecting binary floats outright."""
    if isinstance(value, Decimal):
        result = value
    elif allow_str and isinstance(value, str):
        try:
            result = Decimal(value)
        except ArithmeticError as exc:
            raise InvalidScentError(f"{name} {value!r} is not a decimal") from exc
    else:
        raise InvalidScentError(f"{name} must be a Decimal, got {type(value).__name__}")
    if not result.is_finite():
        raise InvalidScentError(f"{name} must be finite")
    return result


@dataclass(frozen=True, slots=True)
class ScentParams:
    """The three locked pheromone parameters (App F T16, all FIXED)."""

    center_intensity: Decimal = FIXED_CENTER_INTENSITY
    decay: Decimal = FIXED_DECAY
    field_size: int = FIXED_FIELD_SIZE

    def __post_init__(self) -> None:
        require_decimal(self.center_intensity, "center_intensity")
        require_decimal(self.decay, "decay")
        require_int(self.field_size, "field_size", InvalidScentError)
        for name, value, locked in (
            ("center_intensity", self.center_intensity, FIXED_CENTER_INTENSITY),
            ("decay", self.decay, FIXED_DECAY),
            ("field_size", Decimal(self.field_size), Decimal(FIXED_FIELD_SIZE)),
        ):
            if value != locked:
                raise InvalidScentError(f"{name} is FIXED at {locked}, got {value}")
