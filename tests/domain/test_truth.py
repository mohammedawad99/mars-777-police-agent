"""Unit tests for the local authoritative own-truth value object.

`domain.truth` is the frozen owner of own position, step and own barrier
budget (`STATE_OWNERSHIP.md`; PRD01-FR-013/FR-020). It carries the **public**
board so an action can be validated, and it holds no opponent data at all.
"""

import dataclasses

import pytest

from mars777_police.domain.board import Board, Position
from mars777_police.domain.errors import DomainError
from mars777_police.domain.truth import InvalidTruthError, LocalTruth

GRID = 7
LAST = GRID - 1
CENTRE = Position(3, 3)
BOARD = Board(rows=GRID, cols=GRID)


def test_valid_initial_truth() -> None:
    truth = LocalTruth(board=BOARD, own_position=CENTRE)
    assert truth.own_position == CENTRE
    assert truth.completed_steps == 0


def test_an_explicit_step_count_is_accepted() -> None:
    assert LocalTruth(board=BOARD, own_position=CENTRE, completed_steps=7).completed_steps == 7


@pytest.mark.parametrize(
    "cell",
    [Position(-1, 0), Position(0, -1), Position(GRID, 0), Position(0, GRID)],
)
def test_own_position_outside_the_board_is_rejected(cell: Position) -> None:
    with pytest.raises(InvalidTruthError):
        LocalTruth(board=BOARD, own_position=cell)


@pytest.mark.parametrize("value", [-1, -35])
def test_a_negative_step_count_is_rejected(value: int) -> None:
    with pytest.raises(InvalidTruthError):
        LocalTruth(board=BOARD, own_position=CENTRE, completed_steps=value)


@pytest.mark.parametrize("value", ["0", 0.0, None, True])
def test_a_malformed_step_count_is_rejected(value: object) -> None:
    with pytest.raises(InvalidTruthError):
        LocalTruth(board=BOARD, own_position=CENTRE, completed_steps=value)  # type: ignore[arg-type]


def test_malformed_board_and_position_are_rejected() -> None:
    with pytest.raises(InvalidTruthError):
        LocalTruth(board="board", own_position=CENTRE)  # type: ignore[arg-type]
    with pytest.raises(InvalidTruthError):
        LocalTruth(board=BOARD, own_position=(3, 3))  # type: ignore[arg-type]


def test_own_position_on_a_blocked_cell_is_allowed() -> None:
    # A police barrier may be placed on its own cell (BAR-004), so own position
    # need not stay traversable - only in bounds.
    blocked = Board(rows=GRID, cols=GRID, blocked=frozenset({CENTRE}))
    truth = LocalTruth(board=blocked, own_position=CENTRE)
    assert truth.board.is_blocked(truth.own_position)
    assert truth.board.contains(truth.own_position)


def test_truth_is_immutable_with_no_hidden_members() -> None:
    truth = LocalTruth(board=BOARD, own_position=CENTRE)
    with pytest.raises(dataclasses.FrozenInstanceError):
        truth.completed_steps = 1  # type: ignore[misc]
    assert not hasattr(truth, "__dict__")
    assert LocalTruth.__slots__ == ("board", "own_position", "completed_steps")


def test_truth_equality_by_value() -> None:
    assert LocalTruth(board=BOARD, own_position=CENTRE) == LocalTruth(
        board=BOARD, own_position=CENTRE
    )
    assert LocalTruth(board=BOARD, own_position=CENTRE) != LocalTruth(
        board=BOARD, own_position=Position(0, 0)
    )


def test_truth_error_is_a_domain_error() -> None:
    assert issubclass(InvalidTruthError, DomainError)


def test_the_state_is_exactly_the_three_authoritative_facts() -> None:
    names = {f.name for f in dataclasses.fields(LocalTruth)}
    assert names == {"board", "own_position", "completed_steps"}


def test_no_duplicated_barrier_count_or_capability_flag_exists() -> None:
    # STATE_OWNERSHIP anti-duplication rule 2: barriers exist once, in the
    # board's public facts. A local counter could drift from them.
    names = {f.name for f in dataclasses.fields(LocalTruth)}
    for forbidden in (
        "barriers_placed",
        "barriers_remaining",
        "police_barriers",
        "role",
        "can_place_barrier",
        "is_police",
    ):
        assert forbidden not in names
        assert not hasattr(LocalTruth(board=BOARD, own_position=CENTRE), forbidden)


def test_no_opponent_truth_field_exists() -> None:
    names = {f.name for f in dataclasses.fields(LocalTruth)}
    for forbidden in ("opponent_position", "enemy_position", "thief_position", "cop_position"):
        assert forbidden not in names
    assert not hasattr(LocalTruth, "opponent_position")
