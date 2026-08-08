"""Unit tests for deterministic movement legality and legal-move enumeration.

Covers PRD01-FR-004/005 (single-cell, in-bounds), PRD01-AC-003 (all four
edges) and PRD01-AC-004 (a barrier blocks movement). Legality here is
movement-only: no capture, scoring, barrier-placement or scent semantics.
"""

import pytest

from mars777_police.domain.board import Board, Position
from mars777_police.domain.rules import MOVE_ORDER, Move, is_legal_move, legal_moves

GRID = 7
LAST = GRID - 1
CENTRE = Position(3, 3)


def _board(blocked: frozenset[Position] = frozenset()) -> Board:
    return Board(rows=GRID, cols=GRID, blocked=blocked)


@pytest.mark.parametrize(
    ("origin", "move"),
    [
        (Position(0, 3), Move.N),
        (Position(LAST, 3), Move.S),
        (Position(3, 0), Move.W),
        (Position(3, LAST), Move.E),
    ],
)
def test_moves_off_each_edge_are_illegal(origin: Position, move: Move) -> None:
    assert not is_legal_move(_board(), origin, move)


@pytest.mark.parametrize("move", [Move.N, Move.S, Move.E, Move.W])
def test_ordinary_cardinal_moves_are_legal_in_open_space(move: Move) -> None:
    assert is_legal_move(_board(), CENTRE, move)


def test_stay_is_legal_from_a_valid_unblocked_cell() -> None:
    assert is_legal_move(_board(), CENTRE, Move.STAY)


def test_stay_uses_the_same_mechanism_when_the_current_cell_is_blocked() -> None:
    # No special-casing: STAY resolves to the current cell and that cell is
    # evaluated exactly like any other destination.
    board = _board(frozenset({CENTRE}))
    assert not is_legal_move(board, CENTRE, Move.STAY)


def test_move_into_a_blocked_cell_is_illegal() -> None:
    board = _board(frozenset({Position(2, 3)}))
    assert not is_legal_move(board, CENTRE, Move.N)
    assert is_legal_move(board, CENTRE, Move.S)


def test_move_from_an_off_board_cell_is_illegal() -> None:
    for move in MOVE_ORDER:
        assert not is_legal_move(_board(), Position(-1, -1), move)


@pytest.mark.parametrize("value", ["N", None, 1, (0, 1)])
def test_values_outside_the_move_set_are_never_legal(value: object) -> None:
    assert not is_legal_move(_board(), CENTRE, value)  # type: ignore[arg-type]


def test_legal_moves_in_open_space_is_the_full_ordered_alphabet() -> None:
    assert legal_moves(_board(), CENTRE) == MOVE_ORDER


def test_legal_moves_follows_the_stable_project_order() -> None:
    board = _board(frozenset({Position(2, 3), Position(3, 2)}))
    assert legal_moves(board, CENTRE) == (Move.S, Move.E, Move.STAY)


def test_legal_moves_at_a_corner_excludes_off_board_directions() -> None:
    assert legal_moves(_board(), Position(0, 0)) == (Move.S, Move.E, Move.STAY)
    assert legal_moves(_board(), Position(LAST, LAST)) == (Move.N, Move.W, Move.STAY)


def test_legal_moves_never_contains_duplicates() -> None:
    for origin in (CENTRE, Position(0, 0), Position(LAST, LAST), Position(0, LAST)):
        moves = legal_moves(_board(), origin)
        assert len(moves) == len(set(moves))


def test_legal_moves_is_a_tuple_and_a_subsequence_of_move_order() -> None:
    moves = legal_moves(_board(frozenset({Position(2, 3)})), CENTRE)
    assert isinstance(moves, tuple)
    indexes = [MOVE_ORDER.index(m) for m in moves]
    assert indexes == sorted(indexes)


def test_a_fully_enclosed_cell_leaves_only_stay() -> None:
    walls = frozenset(
        {Position(2, 3), Position(4, 3), Position(3, 2), Position(3, 4)},
    )
    assert legal_moves(_board(walls), CENTRE) == (Move.STAY,)


def test_a_blocked_current_cell_leaves_no_legal_move() -> None:
    walls = frozenset(
        {CENTRE, Position(2, 3), Position(4, 3), Position(3, 2), Position(3, 4)},
    )
    assert legal_moves(_board(walls), CENTRE) == ()


def test_legality_does_not_mutate_the_board() -> None:
    blocked = frozenset({Position(2, 3)})
    board = _board(blocked)
    legal_moves(board, CENTRE)
    is_legal_move(board, CENTRE, Move.N)
    assert board.blocked == blocked
    assert board == _board(blocked)


def test_legality_rejects_a_non_board_value() -> None:
    assert not is_legal_move("board", CENTRE, Move.N)  # type: ignore[arg-type]
    assert not is_legal_move(_board(), (3, 3), Move.N)  # type: ignore[arg-type]


def test_a_raw_wire_token_is_not_accepted_as_a_move() -> None:
    # Move is a StrEnum, so "N" compares equal to Move.N; parsing a wire token
    # into a Move belongs to the protocol layer, never to the domain.
    assert Move.N == "N"
    assert not is_legal_move(_board(), CENTRE, "N")  # type: ignore[arg-type]
    assert is_legal_move(_board(), CENTRE, Move("N"))
