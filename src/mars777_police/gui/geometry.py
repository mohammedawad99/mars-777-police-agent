"""Where the board goes, for any legal grid, at any reasonable window size.

Deterministic arithmetic and nothing else: the same snapshot always produces the
same pixels, which is what makes a screenshot usable as academic evidence and a
layout testable without a screen.
"""

from dataclasses import dataclass
from typing import Final

MARGIN: Final[int] = 16
PANEL_WIDTH: Final[int] = 260
BANNER_HEIGHT: Final[int] = 44
MIN_CELL: Final[int] = 24
MAX_CELL: Final[int] = 64


@dataclass(frozen=True, slots=True)
class BoardGeometry:
    """The pixel box of a board, and of each of its cells."""

    left: int
    top: int
    cell: int
    grid_size: int

    @property
    def side(self) -> int:
        """The board's pixel extent, square by construction."""
        return self.cell * self.grid_size

    def cell_box(self, row: int, col: int) -> tuple[int, int, int, int]:
        """The pixel box of one cell: left, top, width, height."""
        return (self.left + col * self.cell, self.top + row * self.cell, self.cell, self.cell)


def fit(grid_size: int, width: int, height: int) -> BoardGeometry:
    """Lay a *grid_size* board into a window, clamped so it stays readable.

    The cell size is bounded at both ends: below `MIN_CELL` a board stops being
    legible, and above `MAX_CELL` a small board turns into decoration. Between
    them it scales, so no monitor resolution is assumed.
    """
    if grid_size <= 0:
        raise ValueError("a board needs at least one row")
    available = min(width - PANEL_WIDTH - 3 * MARGIN, height - BANNER_HEIGHT - 3 * MARGIN)
    cell = max(MIN_CELL, min(MAX_CELL, available // grid_size))
    return BoardGeometry(MARGIN, BANNER_HEIGHT + MARGIN, cell, grid_size)


def window_size(grid_size: int) -> tuple[int, int]:
    """A window that shows a *grid_size* board whole, with room for the panel."""
    board = MAX_CELL * grid_size
    return (board + PANEL_WIDTH + 3 * MARGIN, board + BANNER_HEIGHT + 3 * MARGIN)
