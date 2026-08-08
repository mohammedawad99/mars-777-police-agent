"""Unit tests for the three locked capture routes.

PRD01-FR-050 same-cell · PRD01-FR-051 barrier on the occupied cell (BAR-003)
· PRD01-FR-052 trapped thief (GAME-005). GAME-005 is resolved from the source
itself: PDF p.37 defines "no legal move" as *all adjacent cells* blocked by
barriers and/or the board edge, so STAY is not an escape and does not prevent
the trapped capture. Predicates are pure and hold no state.
"""

import pytest

from mars777_police.domain.board import Board, Position
from mars777_police.domain.errors import DomainError
from mars777_police.domain.rules import Move, apply_move, is_legal_move, legal_moves
from mars777_police.domain.terminal import (
    is_barrier_capture,
    is_same_cell,
    is_trapped,
)

GRID = 7
LAST = GRID - 1
CENTRE = Position(3, 3)
WALLS = frozenset({Position(2, 3), Position(4, 3), Position(3, 2), Position(3, 4)})


def _board(blocked: frozenset[Position] = frozenset()) -> Board:
    return Board(rows=GRID, cols=GRID, blocked=blocked)


def test_same_cell_capture_positive() -> None:
    assert is_same_cell(Position(2, 5), Position(2, 5))


@pytest.mark.parametrize("other", [Position(2, 4), Position(3, 5), Position(0, 0)])
def test_same_cell_capture_negative(other: Position) -> None:
    assert not is_same_cell(Position(2, 5), other)


def test_barrier_capture_positive() -> None:
    # BAR-003: a barrier placed on the occupied cell is a capture.
    assert is_barrier_capture(Position(4, 1), Position(4, 1))


@pytest.mark.parametrize("target", [Position(4, 2), Position(3, 1), Position(0, 0)])
def test_barrier_capture_negative(target: Position) -> None:
    assert not is_barrier_capture(target, Position(4, 1))


def test_trapped_when_all_four_orthogonal_neighbours_are_blocked() -> None:
    assert is_trapped(_board(WALLS), CENTRE)


def test_trapped_control_one_open_neighbour_is_not_trapped() -> None:
    almost = frozenset({Position(2, 3), Position(4, 3), Position(3, 2)})
    assert not is_trapped(_board(almost), CENTRE)


def test_trapped_in_a_corner_uses_board_edges() -> None:
    # GAME-005 counts the board edge exactly like a barrier.
    corner = Position(0, 0)
    assert is_trapped(_board(frozenset({Position(1, 0), Position(0, 1)})), corner)
    assert not is_trapped(_board(frozenset({Position(1, 0)})), corner)


def test_trapped_on_an_open_board_is_false() -> None:
    assert not is_trapped(_board(), CENTRE)
    assert not is_trapped(_board(), Position(0, 0))


def test_stay_does_not_prevent_the_trapped_capture() -> None:
    # Regression for the GAME-005 / STAY resolution: STAY remains a legal
    # Stage-3A move on an unblocked cell, yet the thief is still captured
    # because every ADJACENT cell is blocked (PDF p.37, GAME-005).
    board = _board(WALLS)
    assert is_legal_move(board, CENTRE, Move.STAY)
    assert legal_moves(board, CENTRE) == (Move.STAY,)
    assert is_trapped(board, CENTRE)


def test_stage_3a_legality_was_not_altered_by_stage_3b() -> None:
    board = _board()
    assert legal_moves(board, CENTRE) == (Move.N, Move.S, Move.E, Move.W, Move.STAY)
    assert legal_moves(board, Position(0, 0)) == (Move.S, Move.E, Move.STAY)
    with pytest.raises(DomainError, match="illegal move"):
        apply_move(board, Position(0, 3), Move.N)


def test_trapped_ignores_diagonal_openings() -> None:
    # Diagonals are not adjacencies; an open diagonal does not save the thief.
    assert is_trapped(_board(WALLS), CENTRE)
    assert not _board(WALLS).is_blocked(Position(2, 2))


def test_capture_predicates_hold_no_state() -> None:
    board = _board(WALLS)
    first = (is_trapped(board, CENTRE), is_same_cell(CENTRE, CENTRE))
    for _ in range(5):
        assert (is_trapped(board, CENTRE), is_same_cell(CENTRE, CENTRE)) == first
    assert board.blocked == WALLS


def test_no_dual_truth_structure_is_exposed() -> None:
    from mars777_police.domain import terminal

    exported = set(dir(terminal))
    for forbidden in (
        "GameState",
        "WorldState",
        "MatchState",
        "opponent_position",
        "cop_true_position",
        "thief_true_position",
    ):
        assert forbidden not in exported
