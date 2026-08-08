"""Immutable grid configuration and its Appendix-F validation policy.

Stage 3A implements only the grid part of the locked configuration: the board
is a **square** grid whose size comes from ``board_and_agents.grid_size`` and
which MUST be rejected below 7 (PRD01-FR-001; App F T13 grid_size MINIMUM 7;
conflict C-01). ``MIN_GRID_SIZE`` is a validation floor, not a substitute for
the signed value -- the size itself is always supplied by the caller.

``axis_start_index`` is NEGOTIABLE with default 0 (PRD01-FR-002), so it is
carried here rather than hard-coded into the geometry.

This module performs no I/O: it reads no file and no environment variable.
"""

from collections.abc import Iterable
from dataclasses import dataclass
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
