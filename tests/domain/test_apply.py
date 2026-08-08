"""Unit tests for safe application of a legal move.

Covers PRD01-FR-011 (validation strictly precedes effect) and PRD01-FR-012
(an illegal action leaves authoritative state byte-identical). apply_move is
the effect operation; legality itself is reported by the verdict API.
"""

import pytest

from mars777_police.domain.board import Board, Position
from mars777_police.domain.errors import DomainError
from mars777_police.domain.rules import IllegalMoveError, Move, apply_move

GRID = 7
LAST = GRID - 1
CENTRE = Position(3, 3)


def _board(blocked: frozenset[Position] = frozenset()) -> Board:
    return Board(rows=GRID, cols=GRID, blocked=blocked)


@pytest.mark.parametrize(
    ("move", "expected"),
    [
        (Move.N, Position(2, 3)),
        (Move.S, Position(4, 3)),
        (Move.E, Position(3, 4)),
        (Move.W, Position(3, 2)),
        (Move.STAY, Position(3, 3)),
    ],
)
def test_a_legal_move_returns_the_expected_position(move: Move, expected: Position) -> None:
    assert apply_move(_board(), CENTRE, move) == expected


def test_out_of_bounds_move_raises_a_typed_domain_error() -> None:
    with pytest.raises(IllegalMoveError):
        apply_move(_board(), Position(0, 3), Move.N)


def test_blocked_destination_raises_a_typed_domain_error() -> None:
    board = _board(frozenset({Position(2, 3)}))
    with pytest.raises(IllegalMoveError):
        apply_move(board, CENTRE, Move.N)


@pytest.mark.parametrize("value", ["N", None, 1, (0, 1)])
def test_a_value_outside_the_move_set_raises(value: object) -> None:
    with pytest.raises(IllegalMoveError):
        apply_move(_board(), CENTRE, value)  # type: ignore[arg-type]


def test_illegal_move_error_is_a_domain_error() -> None:
    assert issubclass(IllegalMoveError, DomainError)


def test_the_board_is_unchanged_by_a_successful_move() -> None:
    blocked = frozenset({Position(2, 3)})
    board = _board(blocked)
    apply_move(board, CENTRE, Move.S)
    assert board.blocked == blocked
    assert board == _board(blocked)


def test_the_board_is_unchanged_by_a_rejected_move() -> None:
    blocked = frozenset({Position(2, 3)})
    board = _board(blocked)
    with pytest.raises(IllegalMoveError):
        apply_move(board, CENTRE, Move.N)
    assert board.blocked == blocked
    assert board == _board(blocked)


def test_the_input_position_is_unchanged() -> None:
    origin = Position(3, 3)
    moved = apply_move(_board(), origin, Move.N)
    assert origin == Position(3, 3)
    assert moved is not origin


def test_stay_returns_an_equal_position_without_mutating_it() -> None:
    origin = Position(3, 3)
    assert apply_move(_board(), origin, Move.STAY) == origin
    assert origin == Position(3, 3)


def test_rejection_message_is_deterministic_and_carries_no_secret_state() -> None:
    board = _board()
    messages = []
    for _ in range(3):
        with pytest.raises(IllegalMoveError) as excinfo:
            apply_move(board, Position(0, 3), Move.N)
        messages.append(str(excinfo.value))
    assert len(set(messages)) == 1
    text = messages[0].lower()
    for forbidden in ("nonce", "key", "secret", "token", "opponent", "thief", "police"):
        assert forbidden not in text


def test_every_edge_rejects_the_outward_move() -> None:
    cases = (
        (Position(0, 3), Move.N),
        (Position(LAST, 3), Move.S),
        (Position(3, 0), Move.W),
        (Position(3, LAST), Move.E),
    )
    for origin, move in cases:
        with pytest.raises(IllegalMoveError):
            apply_move(_board(), origin, move)


def test_apply_move_rejects_a_non_position_and_names_no_state() -> None:
    with pytest.raises(IllegalMoveError) as excinfo:
        apply_move(_board(), (3, 3), Move.N)  # type: ignore[arg-type]
    assert "<tuple>" in str(excinfo.value)
