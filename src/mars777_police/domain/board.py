"""Immutable grid geometry: coordinates and the board.

Pure value types with no policy: this module knows where cells are, not which
grid sizes a signed config may declare (that floor lives in ``config_model``)
and not who may block a cell (a later stage). Per
``docs/architecture/MODULE_BOUNDARIES.md`` ``domain.board`` depends on the
standard library only.

Cells are addressed as ``[row, col]`` integers (PRD01-FR-002, JDEC-006). The
valid index range on each axis is ``[start_index, start_index + extent - 1]``
(PRD01-FR-005); ``axis_start_index`` is NEGOTIABLE and therefore supplied, not
hard-coded.
"""

from collections.abc import Iterable
from dataclasses import dataclass, field

from .errors import DomainError, require_int


class InvalidBoardError(DomainError):
    """Raised when coordinates or board geometry are malformed."""


@dataclass(frozen=True, slots=True)
class Position:
    """One immutable cell coordinate.

    Holds exactly the two locked coordinate components. It carries no board
    reference, no role, no opponent data and no rules.
    """

    row: int
    col: int

    def __post_init__(self) -> None:
        require_int(self.row, "row", InvalidBoardError)
        require_int(self.col, "col", InvalidBoardError)


@dataclass(frozen=True, slots=True)
class Board:
    """An immutable board: extent, index origin, and the blocked cells.

    ``blocked`` are supplied domain facts. Whether a placement was legal, who
    made it, and what it means for capture are out of this module's scope.

    Geometry carries no configuration policy: the locked ``>= 7`` floor is
    enforced by ``config_model.GridConfig``, which is the only way a signed
    config reaches a board. Build boards with ``GridConfig.to_board()`` on
    that path; a bare ``Board`` is a geometry primitive for tests and for
    derived positions.
    """

    rows: int
    cols: int
    start_index: int = 0
    blocked: frozenset[Position] = field(default=frozenset())

    def __post_init__(self) -> None:
        require_int(self.rows, "rows", InvalidBoardError)
        require_int(self.cols, "cols", InvalidBoardError)
        require_int(self.start_index, "start_index", InvalidBoardError)
        if self.rows < 1 or self.cols < 1:
            raise InvalidBoardError(
                f"board extent must be positive, got {self.rows}x{self.cols}",
            )
        object.__setattr__(self, "blocked", self._validated_blocked())

    def contains(self, position: Position) -> bool:
        """Return True when *position* lies inside the board."""
        if not isinstance(position, Position):
            return False
        return (
            self.start_index <= position.row <= self.start_index + self.rows - 1
            and self.start_index <= position.col <= self.start_index + self.cols - 1
        )

    def is_blocked(self, position: Position) -> bool:
        """Return True when *position* is a blocked cell."""
        return position in self.blocked

    def is_traversable(self, position: Position) -> bool:
        """Return True when *position* is on the board and not blocked."""
        return self.contains(position) and not self.is_blocked(position)

    def _validated_blocked(self) -> frozenset[Position]:
        raw: object = self.blocked
        if isinstance(raw, str) or not isinstance(raw, Iterable):
            raise InvalidBoardError(
                f"blocked must be an iterable of Position, got {type(raw).__name__}",
            )
        cells: set[Position] = set()
        for cell in raw:
            if not isinstance(cell, Position):
                raise InvalidBoardError(
                    f"blocked cell must be a Position, got {type(cell).__name__}",
                )
            if not self.contains(cell):
                raise InvalidBoardError(
                    f"blocked cell [{cell.row},{cell.col}] lies outside the board",
                )
            cells.add(cell)
        return frozenset(cells)
