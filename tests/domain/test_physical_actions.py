"""The one authoritative physical-action value a turn consists of.

Ch 5 §5.3.1 (p.51) defines the sealed `Move` as *the physical action; the chosen
action (movement, **barrier placement**, etc.)*, and Ch 3 §3.4 (p.37) gives one
single action per turn - one orthogonal cell **or stay** - with a police barrier
only in a turn where movement is forgone. So the domain owns two structurally
exclusive action values, and `domain.rules.Move` stays the movement vocabulary.

Validation here is **structural only** (Stage 4E-R4): exact composed types, no
coercion, and nothing that needs a `Board`. Role, adjacency, bounds, occupancy
and quota are LIVE and belong to the rules and the turn service.
"""

import dataclasses
import inspect

import pytest

from mars777_police.domain import actions as actions_module
from mars777_police.domain.actions import (
    ActionKind,
    BarrierAction,
    InvalidPhysicalActionError,
    MoveAction,
    PhysicalAction,
)
from mars777_police.domain.board import Position
from mars777_police.domain.errors import DomainError
from mars777_police.domain.rules import Move

CELL = Position(2, 3)


def test_the_action_kinds_are_exactly_move_and_barrier() -> None:
    assert [k.value for k in ActionKind] == ["MOVE", "BARRIER"]


def test_each_action_carries_exactly_one_payload_and_derives_its_kind() -> None:
    """`kind` is the class's own answer, never a stored field to disagree with."""
    assert tuple(f.name for f in dataclasses.fields(MoveAction)) == ("move",)
    assert tuple(f.name for f in dataclasses.fields(BarrierAction)) == ("target",)
    assert MoveAction(Move.N).kind is ActionKind.MOVE
    assert BarrierAction(CELL).kind is ActionKind.BARRIER


@pytest.mark.parametrize("absent", ["kind", "target", "role", "board", "step", "position"])
def test_a_movement_action_carries_nothing_further(absent: str) -> None:
    assert absent not in {f.name for f in dataclasses.fields(MoveAction)}


@pytest.mark.parametrize("absent", ["kind", "move", "role", "board", "step", "quota"])
def test_a_barrier_action_carries_nothing_further(absent: str) -> None:
    assert absent not in {f.name for f in dataclasses.fields(BarrierAction)}


def test_the_actions_are_frozen_slotted_and_value_equal() -> None:
    action = MoveAction(Move.N)
    with pytest.raises(dataclasses.FrozenInstanceError):
        action.move = Move.S  # type: ignore[misc]
    assert not hasattr(action, "__dict__")
    assert MoveAction.__slots__ == ("move",)
    assert BarrierAction.__slots__ == ("target",)
    assert MoveAction(Move.N) == MoveAction(Move.N)
    assert MoveAction(Move.N) != MoveAction(Move.S)
    assert BarrierAction(CELL) == BarrierAction(Position(2, 3))
    assert BarrierAction(CELL) != BarrierAction(Position(3, 2))


@pytest.mark.parametrize("value", ["N", "STAY", 0, 1, None, True, object(), Position(1, 1)])
def test_a_movement_of_the_wrong_type_is_refused_never_coerced(value: object) -> None:
    """A valid `"N"` string still raises: `Move` has one authoritative form."""
    with pytest.raises(InvalidPhysicalActionError):
        MoveAction(value)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "value",
    [(2, 3), [2, 3], {"row": 2, "col": 3}, "2,3", None, True, 0, Move.N],
)
def test_a_target_of_the_wrong_type_is_refused_never_coerced(value: object) -> None:
    with pytest.raises(InvalidPhysicalActionError):
        BarrierAction(value)  # type: ignore[arg-type]


def test_a_position_subclass_is_refused() -> None:
    """Exact identity, not `isinstance`: a subclass could weaken validation."""

    class LoosePosition(Position):
        pass

    with pytest.raises(InvalidPhysicalActionError):
        BarrierAction(LoosePosition(2, 3))


def test_a_move_subclass_is_impossible_by_language_rule() -> None:
    """Not a weaker guarantee than `Position`'s - a stronger, enforced one."""
    with pytest.raises(TypeError):

        class LooseMove(Move):  # type: ignore[misc]
            pass


def test_staying_put_is_an_ordinary_movement_never_a_barrier_or_a_non_action() -> None:
    """Ch 3 p.37 lists staying beside the four directions; a barrier forgoes movement."""
    stay = MoveAction(Move.STAY)
    assert stay.kind is ActionKind.MOVE
    assert stay.move is Move.STAY
    assert stay != BarrierAction(CELL)
    assert type(stay) is not BarrierAction


def test_a_barrier_binds_its_exact_cell_and_checks_no_live_rule() -> None:
    """Bounds, adjacency, occupancy, quota and role are all LIVE, not structural."""
    far_off_board = BarrierAction(Position(-40, 999))
    assert far_off_board.target == Position(-40, 999)
    assert BarrierAction(CELL).target is CELL


def test_the_union_is_exactly_the_two_actions_with_no_base_class() -> None:
    assert set(PhysicalAction.__args__) == {MoveAction, BarrierAction}
    assert MoveAction.__mro__[1:] == (object,)
    assert BarrierAction.__mro__[1:] == (object,)


def test_malformed_construction_is_a_domain_failure_not_an_application_one() -> None:
    assert issubclass(InvalidPhysicalActionError, DomainError)
    assert not issubclass(InvalidPhysicalActionError, ValueError)


def test_the_action_module_neither_serializes_nor_reaches_outward() -> None:
    """R4 froze the canonical JSON; encoding it is a later protocol slice."""
    for forbidden in ("json", "hashlib", "to_json", "to_dict", "canonical", "encode"):
        assert not hasattr(actions_module, forbidden)
    for method in ("to_json", "to_dict", "canonical_value", "serialize", "encode"):
        assert not hasattr(MoveAction, method)
        assert not hasattr(BarrierAction, method)
    source = inspect.getsource(actions_module)
    for outward in ("from ..app", "from ..protocol", "from ..infra", "import json"):
        assert outward not in source


def test_the_actions_are_on_the_exhaustive_domain_surface() -> None:
    from mars777_police import domain

    assert domain.MoveAction is MoveAction
    assert domain.BarrierAction is BarrierAction
    assert domain.ActionKind is ActionKind
    assert domain.InvalidPhysicalActionError is InvalidPhysicalActionError
    assert {"ActionKind", "MoveAction", "BarrierAction", "PhysicalAction"} <= set(domain.__all__)
