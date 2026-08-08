"""ROLE-SPECIFIC: the police local service may place barriers (BAR-004).

Placement replaces movement on that turn, so it consumes exactly one local
action and never moves the actor. The board is the only placement record.
"""

import inspect

import pytest

from mars777_police.app import turn_service
from mars777_police.app.turn_service import (
    ActionKind,
    BarrierAction,
    InvalidActionError,
    LocalTurnService,
    MoveAction,
)
from mars777_police.domain.barriers import BarrierQuota
from mars777_police.domain.board import Board, Position
from mars777_police.domain.rules import Move
from mars777_police.domain.terminal import TurnLimits
from mars777_police.domain.truth import LocalTruth

GRID = 7
CENTRE = Position(3, 3)
LIMITS = TurnLimits(max_moves=35, survival_threshold=35)
QUOTA = BarrierQuota(max_barriers=14)


def _service(quota: BarrierQuota = QUOTA) -> LocalTurnService:
    return LocalTurnService(limits=LIMITS, quota=quota)


def _truth(board: Board | None = None) -> LocalTruth:
    return LocalTruth(board=board or Board(rows=GRID, cols=GRID), own_position=CENTRE)


def test_a_barrier_on_the_own_cell_is_accepted() -> None:
    result = _service().apply(_truth(), BarrierAction(CENTRE))
    assert result.kind is ActionKind.BARRIER
    assert result.truth.board.is_blocked(CENTRE)
    assert result.truth.own_position == CENTRE
    assert result.truth.completed_steps == 1
    # The board is the single authoritative record of the placement.
    assert result.truth.board.blocked == frozenset({CENTRE})


@pytest.mark.parametrize("target", [Position(2, 3), Position(4, 3), Position(3, 2), Position(3, 4)])
def test_a_barrier_on_a_cardinal_neighbour_is_accepted(target: Position) -> None:
    result = _service().apply(_truth(), BarrierAction(target))
    assert result.truth.board.is_blocked(target)
    assert result.truth.own_position == CENTRE


def test_a_barrier_never_moves_the_actor_and_leaves_the_input_untouched() -> None:
    before = _truth()
    result = _service().apply(before, BarrierAction(Position(2, 3)))
    assert result.truth.own_position == before.own_position == CENTRE
    assert before.board.blocked == frozenset()
    assert before.completed_steps == 0
    assert result.truth.board is not before.board


@pytest.mark.parametrize("target", [Position(2, 2), Position(1, 3), Position(-1, 3)])
def test_illegal_targets_fail_atomically(target: Position) -> None:
    before = _truth()
    with pytest.raises(InvalidActionError):
        _service().apply(before, BarrierAction(target))
    assert before.board.blocked == frozenset()
    assert before.completed_steps == 0
    assert before.own_position == CENTRE


def test_a_duplicate_barrier_fails_atomically() -> None:
    board = Board(rows=GRID, cols=GRID, blocked=frozenset({Position(2, 3)}))
    before = _truth(board)
    with pytest.raises(InvalidActionError):
        _service().apply(before, BarrierAction(Position(2, 3)))
    assert before.board.blocked == frozenset({Position(2, 3)})
    assert before.completed_steps == 0


def test_an_exhausted_quota_fails_atomically() -> None:
    filled = frozenset(Position(0, c) for c in range(GRID)) | frozenset(
        Position(1, c) for c in range(GRID)
    )
    before = _truth(Board(rows=GRID, cols=GRID, blocked=filled))
    with pytest.raises(InvalidActionError):
        _service().apply(before, BarrierAction(Position(2, 3)))
    assert before.board.blocked == filled
    assert before.completed_steps == 0


def test_own_cell_barrier_sequence_leaves_a_valid_state() -> None:
    service = _service()
    after = service.apply(_truth(), BarrierAction(CENTRE)).truth
    # The state is valid even though the agent now stands on a blocked cell.
    assert after.own_position == CENTRE
    assert after.board.is_blocked(after.own_position)
    assert after.board.contains(after.own_position)
    # STAY is illegal there under the unchanged Stage-3A destination rule.
    with pytest.raises(InvalidActionError):
        service.apply(after, MoveAction(Move.STAY))
    # Moving out to an open cell still works.
    moved = service.apply(after, MoveAction(Move.N))
    assert moved.truth.own_position == Position(2, 3)
    assert moved.truth.completed_steps == 2


def test_placement_delegates_to_the_domain_and_records_only_on_the_board() -> None:
    source = inspect.getsource(turn_service)
    assert "place_barrier" in source
    assert "is_adjacent_or_same" not in source
    result = _service().apply(_truth(), BarrierAction(Position(2, 3)))
    assert len(result.truth.board.blocked) == 1
    assert not hasattr(result.truth, "barriers_placed")


def test_the_quota_stays_authoritative_without_any_application_counter() -> None:
    # A simulated later-game board: 13 cells already blocked by earlier VALID
    # police placements (there is no static-obstacle category in the model, so
    # every blocked cell consumed quota). None is adjacent to the actor, so the
    # 14th placement is accepted and the 15th refused purely on that count.
    thirteen = frozenset(Position(0, c) for c in range(GRID)) | frozenset(
        Position(1, c) for c in range(6)
    )
    assert len(thirteen) == 13
    service = _service(BarrierQuota(max_barriers=14))
    truth = _truth(Board(rows=GRID, cols=GRID, blocked=thirteen))
    truth = service.apply(truth, BarrierAction(Position(2, 3))).truth
    assert len(truth.board.blocked) == 14
    assert truth.completed_steps == 1
    with pytest.raises(InvalidActionError):
        service.apply(truth, BarrierAction(Position(4, 3)))
    assert len(truth.board.blocked) == 14


def test_quota_bounds_come_from_configuration_only() -> None:
    from mars777_police.domain.barriers import InvalidBarrierError

    full = frozenset(Position(0, c) for c in range(GRID)) | frozenset(
        Position(1, c) for c in range(GRID)
    )
    truth = _truth(Board(rows=GRID, cols=GRID, blocked=full))
    assert len(truth.board.blocked) == 14
    wide = _service(BarrierQuota(max_barriers=20))
    assert len(wide.apply(truth, BarrierAction(Position(2, 3))).truth.board.blocked) == 15
    with pytest.raises(InvalidBarrierError):
        BarrierQuota(max_barriers=13)
