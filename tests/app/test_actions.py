"""Unit tests for the local action command model and its result.

PRD01-FR-010: exactly one proposed action is evaluated per turn per agent, so
one command must structurally mean exactly one action - a move OR a barrier,
never both. No wire schema or serialization exists at this stage.
"""

import dataclasses

import pytest

from mars777_police.app.turn_service import (
    ActionKind,
    ApplicationError,
    BarrierAction,
    LocalActionResult,
    MoveAction,
)
from mars777_police.domain.actions import InvalidPhysicalActionError
from mars777_police.domain.board import Position
from mars777_police.domain.rules import Move


def test_action_kinds_are_exactly_move_and_barrier() -> None:
    assert {k.value for k in ActionKind} == {"MOVE", "BARRIER"}


def test_move_action_carries_only_a_move() -> None:
    names = tuple(f.name for f in dataclasses.fields(MoveAction))
    assert names == ("move",)
    assert MoveAction(Move.N).kind is ActionKind.MOVE


def test_barrier_action_carries_only_a_target() -> None:
    names = tuple(f.name for f in dataclasses.fields(BarrierAction))
    assert names == ("target",)
    assert BarrierAction(Position(2, 3)).kind is ActionKind.BARRIER


def test_no_command_can_express_both_a_move_and_a_barrier() -> None:
    # Structural guarantee: neither command type has a field of the other kind.
    move_fields = {f.name for f in dataclasses.fields(MoveAction)}
    barrier_fields = {f.name for f in dataclasses.fields(BarrierAction)}
    assert move_fields & barrier_fields == set()
    assert "target" not in move_fields
    assert "move" not in barrier_fields
    with pytest.raises(TypeError):
        MoveAction(move=Move.N, target=Position(2, 3))  # type: ignore[call-arg]
    with pytest.raises(TypeError):
        BarrierAction(target=Position(2, 3), move=Move.N)  # type: ignore[call-arg]


def test_actions_are_immutable() -> None:
    action = MoveAction(Move.N)
    with pytest.raises(dataclasses.FrozenInstanceError):
        action.move = Move.S  # type: ignore[misc]
    assert not hasattr(action, "__dict__")


def test_actions_reject_wrong_payload_types() -> None:
    """Structural construction is a *domain* failure since Stage 4E-R5."""
    with pytest.raises(InvalidPhysicalActionError):
        MoveAction("N")  # type: ignore[arg-type]
    with pytest.raises(InvalidPhysicalActionError):
        BarrierAction((2, 3))  # type: ignore[arg-type]


def test_actions_are_equal_by_value() -> None:
    assert MoveAction(Move.N) == MoveAction(Move.N)
    assert MoveAction(Move.N) != MoveAction(Move.S)
    assert BarrierAction(Position(2, 3)) == BarrierAction(Position(2, 3))
    assert MoveAction(Move.N) != BarrierAction(Position(2, 3))


def test_result_carries_only_local_facts() -> None:
    names = {f.name for f in dataclasses.fields(LocalActionResult)}
    assert names == {"truth", "kind", "completed_step"}
    for forbidden in (
        "score",
        "outcome",
        "opponent_position",
        "nonce",
        "commitment",
        "message",
        "artifact",
        "scent",
        "hash",
    ):
        assert forbidden not in names


def test_result_is_immutable() -> None:
    from mars777_police.domain.board import Board
    from mars777_police.domain.truth import LocalTruth

    result = LocalActionResult(
        truth=LocalTruth(board=Board(rows=7, cols=7), own_position=Position(3, 3)),
        kind=ActionKind.MOVE,
        completed_step=1,
    )
    with pytest.raises(dataclasses.FrozenInstanceError):
        result.completed_step = 2  # type: ignore[misc]


def test_the_service_rejects_a_non_truth_argument() -> None:
    from mars777_police.app.turn_service import LocalTurnService
    from mars777_police.domain.barriers import BarrierQuota
    from mars777_police.domain.rules import Move
    from mars777_police.domain.terminal import TurnLimits

    service = LocalTurnService(
        limits=TurnLimits(max_moves=35, survival_threshold=35),
        quota=BarrierQuota(max_barriers=14),
    )
    with pytest.raises(ApplicationError):
        service.apply("truth", MoveAction(Move.N))  # type: ignore[arg-type]


def test_the_service_rejects_an_unknown_action_object() -> None:
    from mars777_police.app.turn_service import LocalTurnService, UnsupportedActionError
    from mars777_police.domain.barriers import BarrierQuota
    from mars777_police.domain.board import Board
    from mars777_police.domain.terminal import TurnLimits
    from mars777_police.domain.truth import LocalTruth

    service = LocalTurnService(
        limits=TurnLimits(max_moves=35, survival_threshold=35),
        quota=BarrierQuota(max_barriers=14),
    )
    truth = LocalTruth(board=Board(rows=7, cols=7), own_position=Position(3, 3))
    with pytest.raises(UnsupportedActionError):
        service.apply(truth, "MOVE N")  # type: ignore[arg-type]
    assert truth.completed_steps == 0


def test_the_app_action_names_are_the_domain_classes_not_copies() -> None:
    """One definition, possibly two import paths - never two classes."""
    from mars777_police.app import turn_service
    from mars777_police.domain import actions

    assert turn_service.MoveAction is actions.MoveAction
    assert turn_service.BarrierAction is actions.BarrierAction
    assert turn_service.ActionKind is actions.ActionKind
