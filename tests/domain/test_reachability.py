"""Barrier-aware reachability, as the one distance authority a strategy may use.

Every assertion here is about *semantic* distance, never about the order cells
happen to be discovered in: a BFS whose answers depended on traversal order
would hand the strategy a decision that Python's hashing could change between
runs. The primitive therefore reuses `Board.orthogonal_neighbours` and
`Board.is_traversable` rather than carrying its own geometry, and the tests pin
that the answers survive a reordered barrier set.
"""

from mars777_police.domain.board import Board, Position
from mars777_police.domain.reachability import reachable_from

GRID = 7
CENTRE = Position(3, 3)


def _board(*blocked: Position) -> Board:
    return Board(rows=GRID, cols=GRID, blocked=frozenset(blocked))


def test_an_open_board_is_wholly_reachable_from_anywhere_on_it() -> None:
    assert len(reachable_from(_board(), CENTRE)) == GRID * GRID


def test_the_origin_stands_at_distance_zero() -> None:
    assert reachable_from(_board(), CENTRE)[CENTRE] == 0


def test_a_cardinal_neighbour_stands_at_distance_one() -> None:
    depths = reachable_from(_board(), CENTRE)
    for neighbour in _board().orthogonal_neighbours(CENTRE):
        assert depths[neighbour] == 1


def test_distance_on_an_open_board_is_the_manhattan_distance() -> None:
    depths = reachable_from(_board(), Position(0, 0))
    assert depths[Position(6, 6)] == 12
    assert depths[Position(2, 5)] == 7


def test_a_barrier_is_never_reachable_and_never_carries_a_distance() -> None:
    wall = Position(3, 4)
    assert wall not in reachable_from(_board(wall), CENTRE)


def test_a_wall_lengthens_the_route_rather_than_severing_it() -> None:
    wall = tuple(Position(row, 3) for row in range(GRID - 1))
    depths = reachable_from(_board(*wall), Position(3, 0))
    assert depths[Position(3, 6)] == 3 + 6 + 3


def test_a_sealed_pocket_reaches_only_itself() -> None:
    seal = (Position(0, 1), Position(1, 0), Position(1, 1))
    assert reachable_from(_board(*seal), Position(0, 0)) == {Position(0, 0): 0}


def test_cells_beyond_a_full_partition_are_absent_rather_than_infinite() -> None:
    wall = tuple(Position(row, 3) for row in range(GRID))
    depths = reachable_from(_board(*wall), Position(3, 0))
    assert len(depths) == GRID * 3
    assert Position(3, 6) not in depths


def test_an_origin_that_cannot_be_occupied_reaches_nothing() -> None:
    assert reachable_from(_board(CENTRE), CENTRE) == {}


def test_an_origin_outside_the_board_reaches_nothing() -> None:
    assert reachable_from(_board(), Position(9, 9)) == {}


def test_the_answer_does_not_depend_on_the_order_barriers_were_supplied_in() -> None:
    cells = (Position(2, 3), Position(3, 4), Position(4, 3), Position(1, 1))
    first = reachable_from(Board(rows=GRID, cols=GRID, blocked=frozenset(cells)), CENTRE)
    for rotation in range(len(cells)):
        shuffled = cells[rotation:] + cells[:rotation]
        board = Board(rows=GRID, cols=GRID, blocked=frozenset(shuffled))
        assert reachable_from(board, CENTRE) == first


def test_repeated_calls_agree_with_themselves() -> None:
    board = _board(Position(2, 2), Position(4, 4))
    first = reachable_from(board, CENTRE)
    for _ in range(5):
        assert reachable_from(board, CENTRE) == first


def test_it_mutates_neither_the_board_nor_its_barrier_set() -> None:
    blocked = frozenset({Position(2, 2)})
    board = Board(rows=GRID, cols=GRID, blocked=blocked)
    reachable_from(board, CENTRE)
    assert board.blocked == blocked
    assert board == Board(rows=GRID, cols=GRID, blocked=blocked)


def test_the_returned_map_is_a_fresh_object_the_caller_owns() -> None:
    board = _board()
    first = reachable_from(board, CENTRE)
    first.clear()
    assert len(reachable_from(board, CENTRE)) == GRID * GRID
