"""The three capture routes, answered from own truth and public facts only."""

import pytest

from mars777_police.app.capture_rules import adopt_barrier, answer_for_barrier, answer_for_claim
from mars777_police.app.capture_values import CaptureAnswer, CaptureClaim
from mars777_police.domain.board import Board, Position

BOARD = Board(rows=5, cols=5)
HERE = Position(2, 2)


def on_board(board: Board, position: Position) -> tuple[Position, ...]:
    """The neighbours that exist; the edge already blocks the rest."""
    return tuple(cell for cell in board.orthogonal_neighbours(position) if board.contains(cell))


def caged(position: Position, board: Board = BOARD) -> Board:
    """Every reachable neighbour of *position* blocked - the source's cage."""
    return Board(
        rows=board.rows,
        cols=board.cols,
        start_index=board.start_index,
        blocked=frozenset(on_board(board, position)),
    )


def test_a_claim_on_our_cell_is_caught_and_anywhere_else_is_not() -> None:
    assert answer_for_claim(CaptureClaim(HERE), HERE) is CaptureAnswer.CAUGHT
    assert answer_for_claim(CaptureClaim(Position(2, 3)), HERE) is CaptureAnswer.NOT_CAUGHT


def test_a_barrier_on_our_cell_captures_without_any_claim() -> None:
    assert answer_for_barrier(BOARD, HERE, HERE) is CaptureAnswer.CAUGHT


def test_a_barrier_that_misses_asks_nothing() -> None:
    """No declaration was made, so a miss is not a false claim."""
    assert answer_for_barrier(BOARD, Position(0, 0), HERE) is CaptureAnswer.NO_QUESTION


def test_the_barrier_that_closes_the_last_escape_captures() -> None:
    open_cage = Board(rows=5, cols=5, blocked=frozenset({Position(1, 2), Position(3, 2)}))
    assert answer_for_barrier(open_cage, Position(2, 1), HERE) is CaptureAnswer.NO_QUESTION
    almost = Board(
        rows=5, cols=5, blocked=frozenset({Position(1, 2), Position(3, 2), Position(2, 1)})
    )
    assert answer_for_barrier(almost, Position(2, 3), HERE) is CaptureAnswer.CAUGHT


@pytest.mark.parametrize("corner", [Position(0, 0), Position(0, 4), Position(4, 0), Position(4, 4)])
def test_a_corner_needs_only_its_two_neighbours_closed(corner: Position) -> None:
    """The edge counts exactly like a barrier, so a corner has two ways out."""
    neighbours = on_board(BOARD, corner)
    assert len(neighbours) == 2
    partial = Board(rows=5, cols=5, blocked=frozenset(neighbours[:1]))
    assert answer_for_barrier(partial, neighbours[1], corner) is CaptureAnswer.CAUGHT


def test_staying_still_is_not_an_escape() -> None:
    """`STAY` is representable, and GAME-005 does not care."""
    assert answer_for_barrier(caged(HERE, BOARD), HERE, HERE) is CaptureAnswer.CAUGHT
    already = caged(HERE)
    assert answer_for_barrier(already, Position(0, 0), HERE) is CaptureAnswer.CAUGHT


def test_adopting_a_barrier_blocks_the_cell_for_both_sides() -> None:
    adopted = adopt_barrier(BOARD, Position(1, 1))
    assert adopted.is_blocked(Position(1, 1))
    assert not adopted.is_traversable(Position(1, 1))
    assert BOARD.blocked == frozenset()


def test_a_barrier_off_the_board_is_refused() -> None:
    with pytest.raises(ValueError, match="on the board"):
        adopt_barrier(BOARD, Position(9, 9))


def test_the_answer_never_carries_a_position() -> None:
    for answer in (
        answer_for_claim(CaptureClaim(HERE), HERE),
        answer_for_barrier(BOARD, HERE, HERE),
        answer_for_barrier(BOARD, Position(0, 0), HERE),
    ):
        assert isinstance(answer, CaptureAnswer)
        assert answer.value in {"CAUGHT", "NOT_CAUGHT", "NO_QUESTION"}
