"""Unit tests for the movement vocabulary.

Covers PRD01-FR-003 (move_set is exactly N/S/E/W/STAY), PRD01-FR-004
(one cell, one axis, never diagonal) and the project-deterministic
iteration order used by legal-move enumeration.
"""

import pytest

from mars777_police.domain.board import Position
from mars777_police.domain.rules import (
    MOVE_ORDER,
    IllegalMoveError,
    Move,
    delta_of,
    destination_of,
)

EXPECTED_TOKENS = ("N", "S", "E", "W", "STAY")


def test_move_set_is_exactly_five_tokens() -> None:
    assert {m.value for m in Move} == set(EXPECTED_TOKENS)
    assert len(list(Move)) == 5


def test_move_order_is_a_stable_tuple() -> None:
    # Project-deterministic iteration order (not an extra book numeric rule).
    assert isinstance(MOVE_ORDER, tuple)
    assert tuple(m.value for m in MOVE_ORDER) == EXPECTED_TOKENS


def test_move_order_covers_every_move_exactly_once() -> None:
    assert len(MOVE_ORDER) == len(set(MOVE_ORDER)) == len(list(Move))


@pytest.mark.parametrize(
    ("move", "delta"),
    [
        (Move.N, (-1, 0)),
        (Move.S, (1, 0)),
        (Move.E, (0, 1)),
        (Move.W, (0, -1)),
        (Move.STAY, (0, 0)),
    ],
)
def test_deltas_are_exact(move: Move, delta: tuple[int, int]) -> None:
    assert delta_of(move) == delta


def test_no_move_is_diagonal_or_multi_cell() -> None:
    for move in MOVE_ORDER:
        d_row, d_col = delta_of(move)
        assert abs(d_row) <= 1 and abs(d_col) <= 1
        # PRD01-FR-004: never both axes at once.
        assert d_row == 0 or d_col == 0
        if move is not Move.STAY:
            assert abs(d_row) + abs(d_col) == 1


def test_stay_has_zero_delta() -> None:
    assert delta_of(Move.STAY) == (0, 0)


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
def test_destination_is_one_cell_away(move: Move, expected: Position) -> None:
    assert destination_of(Position(3, 3), move) == expected


def test_destination_does_not_mutate_the_source_position() -> None:
    origin = Position(3, 3)
    destination_of(origin, Move.N)
    assert origin == Position(3, 3)


@pytest.mark.parametrize("token", ["NE", "SW", "n", "", "STAY ", "UP"])
def test_tokens_outside_the_move_set_are_not_moves(token: str) -> None:
    # Diagonal and any other token is not part of move_set (GAME-004).
    with pytest.raises(ValueError, match="is not a valid"):
        Move(token)


@pytest.mark.parametrize("value", ["N", None, 1, (0, 1), Position(0, 0)])
def test_non_move_values_raise_a_typed_error(value: object) -> None:
    with pytest.raises(IllegalMoveError):
        delta_of(value)  # type: ignore[arg-type]
    with pytest.raises(IllegalMoveError):
        destination_of(Position(3, 3), value)  # type: ignore[arg-type]


def test_destination_requires_a_position() -> None:
    with pytest.raises(IllegalMoveError):
        destination_of((3, 3), Move.N)  # type: ignore[arg-type]
