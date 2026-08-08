"""Move-action semantics of the local turn service (role-neutral behaviour).

The service is the LOCAL EFFECT step only: it validates through the existing
domain rules, never reimplements them, and advances own truth. It performs no
peer exchange, declares no outcome and produces no score.
"""

import pytest

from mars777_police.app.turn_service import (
    ActionKind,
    ActionsExhaustedError,
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
LAST = GRID - 1
CENTRE = Position(3, 3)
LIMITS = TurnLimits(max_moves=35, survival_threshold=35)
QUOTA = BarrierQuota(max_barriers=14)


def _service() -> LocalTurnService:
    return LocalTurnService(limits=LIMITS, quota=QUOTA)


def _truth(board: Board | None = None, steps: int = 0) -> LocalTruth:
    return LocalTruth(
        board=board or Board(rows=GRID, cols=GRID),
        own_position=CENTRE,
        completed_steps=steps,
    )


@pytest.mark.parametrize(
    ("move", "expected"),
    [
        (Move.N, Position(2, 3)),
        (Move.S, Position(4, 3)),
        (Move.E, Position(3, 4)),
        (Move.W, Position(3, 2)),
    ],
)
def test_a_legal_move_returns_a_new_truth(move: Move, expected: Position) -> None:
    before = _truth()
    result = _service().apply(before, MoveAction(move))
    assert result.truth.own_position == expected
    assert result.truth.completed_steps == 1
    assert result.kind is ActionKind.MOVE
    assert result.completed_step == 1


def test_the_previous_truth_is_unchanged() -> None:
    before = _truth()
    result = _service().apply(before, MoveAction(Move.N))
    assert before.own_position == CENTRE
    assert before.completed_steps == 0
    assert result.truth is not before


def test_a_move_never_changes_the_board() -> None:
    before = _truth()
    result = _service().apply(before, MoveAction(Move.N))
    assert result.truth.board == before.board
    assert result.truth.board.blocked == frozenset()


def test_stay_keeps_the_position_and_still_consumes_one_step() -> None:
    result = _service().apply(_truth(), MoveAction(Move.STAY))
    assert result.truth.own_position == CENTRE
    assert result.truth.completed_steps == 1


def test_each_accepted_action_advances_exactly_one_step() -> None:
    service, truth = _service(), _truth()
    for expected in (1, 2, 3):
        truth = service.apply(truth, MoveAction(Move.STAY)).truth
        assert truth.completed_steps == expected


def test_an_illegal_edge_move_fails_atomically() -> None:
    before = LocalTruth(board=Board(rows=GRID, cols=GRID), own_position=Position(0, 3))
    with pytest.raises(InvalidActionError):
        _service().apply(before, MoveAction(Move.N))
    assert before.own_position == Position(0, 3)
    assert before.completed_steps == 0


def test_a_blocked_destination_fails_atomically() -> None:
    board = Board(rows=GRID, cols=GRID, blocked=frozenset({Position(2, 3)}))
    before = _truth(board)
    with pytest.raises(InvalidActionError):
        _service().apply(before, MoveAction(Move.N))
    assert before.completed_steps == 0
    assert before.board.blocked == frozenset({Position(2, 3)})


def test_no_action_is_accepted_once_the_move_ceiling_is_reached() -> None:
    exhausted = _truth(steps=LIMITS.max_moves)
    with pytest.raises(ActionsExhaustedError):
        _service().apply(exhausted, MoveAction(Move.STAY))
    assert exhausted.completed_steps == LIMITS.max_moves


def test_the_service_uses_configured_limits_not_hard_coded_numbers() -> None:
    wide = LocalTurnService(limits=TurnLimits(max_moves=40, survival_threshold=35), quota=QUOTA)
    truth = _truth(steps=35)
    assert wide.apply(truth, MoveAction(Move.STAY)).truth.completed_steps == 36
