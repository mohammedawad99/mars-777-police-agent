"""Unit tests for immutable positions and the immutable board.

Covers PRD01-FR-002 (cells addressed as [row, col]), PRD01-FR-005 (bounds)
and PRD01-NFR-001 (immutable, pure value types). Blocked cells are supplied
domain facts here; who may place one is out of Stage-3A scope.
"""

import dataclasses

import pytest

from mars777_police.domain.board import Board, InvalidBoardError, Position
from mars777_police.domain.errors import DomainError

GRID = 7
LAST = GRID - 1


def _board(blocked: frozenset[Position] = frozenset()) -> Board:
    return Board(rows=GRID, cols=GRID, blocked=blocked)


def test_position_carries_exactly_row_and_col() -> None:
    names = tuple(f.name for f in dataclasses.fields(Position))
    assert names == ("row", "col")


def test_position_equality_and_hashability() -> None:
    assert Position(2, 3) == Position(2, 3)
    assert Position(2, 3) != Position(3, 2)
    assert len({Position(2, 3), Position(2, 3), Position(3, 2)}) == 2


def test_position_is_immutable_with_no_hidden_members() -> None:
    pos = Position(1, 1)
    with pytest.raises(dataclasses.FrozenInstanceError):
        pos.row = 2  # type: ignore[misc]
    # Slots: no instance __dict__, so no hidden mutable member can be attached.
    assert not hasattr(pos, "__dict__")
    assert Position.__slots__ == ("row", "col")


@pytest.mark.parametrize("value", ["1", 1.0, None, True, [1]])
def test_position_rejects_non_integer_coordinates(value: object) -> None:
    with pytest.raises(InvalidBoardError):
        Position(value, 1)  # type: ignore[arg-type]
    with pytest.raises(InvalidBoardError):
        Position(1, value)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "cell",
    [Position(0, 0), Position(0, LAST), Position(LAST, 0), Position(LAST, LAST)],
)
def test_all_four_corners_are_in_bounds(cell: Position) -> None:
    assert _board().contains(cell)


@pytest.mark.parametrize(
    "cell",
    [
        Position(-1, 0),
        Position(0, -1),
        Position(GRID, 0),
        Position(0, GRID),
        Position(-1, -1),
        Position(GRID, GRID),
    ],
)
def test_outside_cells_are_not_in_bounds(cell: Position) -> None:
    assert not _board().contains(cell)


def test_start_index_shifts_the_valid_range() -> None:
    board = Board(rows=GRID, cols=GRID, start_index=1)
    assert not board.contains(Position(0, 0))
    assert board.contains(Position(1, 1))
    assert board.contains(Position(GRID, GRID))
    assert not board.contains(Position(GRID + 1, GRID))


def test_blocked_cells_are_detected() -> None:
    board = _board(frozenset({Position(3, 3)}))
    assert board.is_blocked(Position(3, 3))
    assert not board.is_blocked(Position(3, 4))


def test_traversable_requires_in_bounds_and_unblocked() -> None:
    board = _board(frozenset({Position(3, 3)}))
    assert board.is_traversable(Position(3, 4))
    assert not board.is_traversable(Position(3, 3))
    assert not board.is_traversable(Position(-1, 0))


def test_blocked_cell_outside_the_grid_is_rejected() -> None:
    with pytest.raises(InvalidBoardError):
        _board(frozenset({Position(GRID, 0)}))
    with pytest.raises(InvalidBoardError):
        _board(frozenset({Position(-1, -1)}))


def test_malformed_blocked_input_is_rejected() -> None:
    with pytest.raises(InvalidBoardError):
        Board(rows=GRID, cols=GRID, blocked=frozenset({(3, 3)}))  # type: ignore[arg-type]
    with pytest.raises(InvalidBoardError):
        Board(rows=GRID, cols=GRID, blocked=42)  # type: ignore[arg-type]


def test_blocked_collection_is_normalised_to_a_frozenset() -> None:
    board = Board(rows=GRID, cols=GRID, blocked=[Position(1, 1), Position(1, 1)])  # type: ignore[arg-type]
    assert board.blocked == frozenset({Position(1, 1)})
    assert isinstance(board.blocked, frozenset)


@pytest.mark.parametrize(("rows", "cols"), [(0, 7), (7, 0), (-1, 7), (7, -1)])
def test_board_requires_positive_extent(rows: int, cols: int) -> None:
    with pytest.raises(InvalidBoardError):
        Board(rows=rows, cols=cols)


@pytest.mark.parametrize("value", ["7", 7.0, None, True])
def test_board_rejects_malformed_geometry(value: object) -> None:
    with pytest.raises(InvalidBoardError):
        Board(rows=value, cols=GRID)  # type: ignore[arg-type]
    with pytest.raises(InvalidBoardError):
        Board(rows=GRID, cols=GRID, start_index=value)  # type: ignore[arg-type]


def test_board_is_immutable_and_comparable() -> None:
    board = _board()
    with pytest.raises(dataclasses.FrozenInstanceError):
        board.rows = 9  # type: ignore[misc]
    assert board == _board()
    assert len({_board(), _board()}) == 1


def test_invalid_board_error_is_a_domain_error() -> None:
    assert issubclass(InvalidBoardError, DomainError)


def test_contains_rejects_a_non_position_value() -> None:
    assert not _board().contains((0, 0))  # type: ignore[arg-type]
    assert not _board().contains(None)  # type: ignore[arg-type]
