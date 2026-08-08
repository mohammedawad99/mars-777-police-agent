"""Unit tests for deterministic barrier-placement semantics.

Covers BAR-004 (own or orthogonally-adjacent cell, on a turn movement is
forgone), BAR-005 / App F T15 #2 (quota, MINIMUM 14) and PRD01-FR-030…034.
Placement authorisation of the caller is not a domain concern; both roles run
the identical verification logic on the publicly declared placement (BAR-001).
"""

import dataclasses

import pytest

from mars777_police.domain.barriers import (
    MIN_MAX_BARRIERS,
    ORTHOGONAL_OFFSETS,
    BarrierQuota,
    InvalidBarrierError,
    is_placeable,
    place_barrier,
)
from mars777_police.domain.board import Board, Position
from mars777_police.domain.errors import DomainError
from mars777_police.domain.rules import Move, delta_of

GRID = 7
LAST = GRID - 1
ACTOR = Position(3, 3)
QUOTA = BarrierQuota(max_barriers=14)


def _board(blocked: frozenset[Position] = frozenset()) -> Board:
    return Board(rows=GRID, cols=GRID, blocked=blocked)


def test_minimum_quota_is_the_locked_floor() -> None:
    assert MIN_MAX_BARRIERS == 14


@pytest.mark.parametrize("value", [13, 0, -1])
def test_quota_below_the_locked_minimum_is_rejected(value: int) -> None:
    with pytest.raises(InvalidBarrierError):
        BarrierQuota(max_barriers=value)


@pytest.mark.parametrize("value", ["14", 14.0, None, True])
def test_malformed_quota_is_rejected(value: object) -> None:
    with pytest.raises(InvalidBarrierError):
        BarrierQuota(max_barriers=value)  # type: ignore[arg-type]


def test_quota_at_and_above_the_minimum_is_accepted() -> None:
    assert BarrierQuota(max_barriers=14).max_barriers == 14
    assert BarrierQuota(max_barriers=20).max_barriers == 20


def test_quota_is_immutable() -> None:
    with pytest.raises(dataclasses.FrozenInstanceError):
        QUOTA.max_barriers = 20  # type: ignore[misc]


def test_orthogonal_offsets_match_the_locked_move_deltas() -> None:
    # The placement neighbourhood must never drift from the movement vocabulary.
    assert tuple(delta_of(m) for m in (Move.N, Move.S, Move.E, Move.W)) == ORTHOGONAL_OFFSETS


def test_placement_on_the_actor_own_cell_is_legal() -> None:
    assert is_placeable(_board(), ACTOR, ACTOR, QUOTA)


@pytest.mark.parametrize(
    "target",
    [Position(2, 3), Position(4, 3), Position(3, 4), Position(3, 2)],
)
def test_placement_on_an_orthogonally_adjacent_cell_is_legal(target: Position) -> None:
    assert is_placeable(_board(), ACTOR, target, QUOTA)


@pytest.mark.parametrize(
    "target",
    [Position(2, 2), Position(2, 4), Position(4, 2), Position(4, 4)],
)
def test_diagonal_placement_is_rejected(target: Position) -> None:
    assert not is_placeable(_board(), ACTOR, target, QUOTA)


@pytest.mark.parametrize("target", [Position(1, 3), Position(5, 3), Position(3, 1), Position(3, 5)])
def test_two_away_placement_is_rejected(target: Position) -> None:
    assert not is_placeable(_board(), ACTOR, target, QUOTA)


def test_placement_outside_the_board_is_rejected() -> None:
    edge = Position(0, 0)
    assert not is_placeable(_board(), edge, Position(-1, 0), QUOTA)
    assert not is_placeable(_board(), Position(LAST, LAST), Position(GRID, LAST), QUOTA)


def test_duplicate_placement_is_rejected() -> None:
    board = _board(frozenset({Position(2, 3)}))
    assert not is_placeable(board, ACTOR, Position(2, 3), QUOTA)


def test_placement_at_the_quota_boundary() -> None:
    quota = BarrierQuota(max_barriers=14)
    row0 = frozenset(Position(0, c) for c in range(GRID))
    filled = row0 | frozenset(Position(1, c) for c in range(GRID))
    assert len(filled) == 14
    board = Board(rows=GRID, cols=GRID, blocked=filled)
    assert not is_placeable(board, ACTOR, Position(2, 3), quota)
    with pytest.raises(InvalidBarrierError):
        place_barrier(board, ACTOR, Position(2, 3), quota)


def test_placement_just_below_the_quota_is_allowed() -> None:
    row0 = frozenset(Position(0, c) for c in range(GRID))
    thirteen = row0 | frozenset(Position(1, c) for c in range(6))
    assert len(thirteen) == 13
    board = Board(rows=GRID, cols=GRID, blocked=thirteen)
    assert is_placeable(board, ACTOR, Position(2, 3), BarrierQuota(max_barriers=14))


def test_place_barrier_returns_a_new_board_and_leaves_the_original_unchanged() -> None:
    board = _board()
    updated = place_barrier(board, ACTOR, Position(2, 3), QUOTA)
    assert updated is not board
    assert board.blocked == frozenset()
    assert updated.blocked == frozenset({Position(2, 3)})
    assert (updated.rows, updated.cols, updated.start_index) == (GRID, GRID, 0)


def test_illegal_placement_raises_and_changes_nothing() -> None:
    board = _board()
    with pytest.raises(InvalidBarrierError):
        place_barrier(board, ACTOR, Position(2, 2), QUOTA)
    assert board.blocked == frozenset()


def test_barrier_error_is_a_domain_error() -> None:
    assert issubclass(InvalidBarrierError, DomainError)


def test_no_public_removal_api_exists() -> None:
    from mars777_police.domain import barriers

    exported = set(dir(barriers))
    for forbidden in ("remove_barrier", "clear_barriers", "unplace", "relocate_barrier"):
        assert forbidden not in exported
