"""The two sub-mappings a sealed record is assembled from (Stage 4E-R9-RESUME).

`move` and `state` are the only sealed members that are not a bare scalar, so
each gets an explicit mapper. Both are written out by hand: a reflective encoder
would silently follow any field a value grows later, and the whole point of these
shapes is that they cannot grow. The action mapping is NDEC-001's tagged object;
the state mapping is JDEC-012's five keys, emitted in the order `SealedState`
already fixed - the mapper never re-sorts, because the ordering decision was
deliberately pushed down into the value.
"""

import pytest

from mars777_police.app.protocol_values import Sha256Digest
from mars777_police.app.sealed_record_values import ActorRole, SealedState
from mars777_police.domain.actions import BarrierAction, MoveAction
from mars777_police.domain.board import Position
from mars777_police.domain.rules import Move
from mars777_police.protocol.commitment import canonical_action_value, canonical_state_value

STATE = SealedState(
    config_sha256=Sha256Digest("1" * 64),
    self_pos=Position(3, 4),
    barriers=(Position(0, 0), Position(2, 2)),
    step=3,
    role=ActorRole.POLICE,
)


@pytest.mark.parametrize("move", list(Move))
def test_every_movement_token_maps_to_the_frozen_tagged_object(move: Move) -> None:
    assert canonical_action_value(MoveAction(move)) == {"kind": "MOVE", "value": move.value}


def test_the_five_movement_tokens_are_exactly_the_locked_alphabet() -> None:
    assert [canonical_action_value(MoveAction(m))["value"] for m in Move] == [
        "N",
        "S",
        "E",
        "W",
        "STAY",
    ]


def test_a_barrier_maps_to_its_exact_placed_cell() -> None:
    """The cell is copied, never derived from position, direction or context."""
    assert canonical_action_value(BarrierAction(Position(5, 6))) == {
        "kind": "BARRIER",
        "value": [5, 6],
    }
    assert canonical_action_value(BarrierAction(Position(0, 0))) == {
        "kind": "BARRIER",
        "value": [0, 0],
    }


def test_an_action_mapping_carries_exactly_two_keys() -> None:
    for action in (MoveAction(Move.W), BarrierAction(Position(1, 2))):
        assert set(canonical_action_value(action)) == {"kind", "value"}


@pytest.mark.parametrize(
    "bad", ["N", Move.N, None, True, 0, Position(1, 2), ("MOVE", "N"), {"kind": "MOVE"}]
)
def test_an_unsupported_action_is_refused(bad: object) -> None:
    with pytest.raises(ValueError):
        canonical_action_value(bad)  # type: ignore[arg-type]


def test_an_action_subclass_is_refused() -> None:
    class LooseMove(MoveAction): ...

    with pytest.raises(ValueError):
        canonical_action_value(LooseMove(Move.N))


def test_the_state_maps_to_exactly_the_five_locked_keys() -> None:
    mapped = canonical_state_value(STATE)
    assert set(mapped) == {"config_sha256", "self_pos", "barriers", "step", "role"}
    assert mapped == {
        "config_sha256": "1" * 64,
        "self_pos": [3, 4],
        "barriers": [[0, 0], [2, 2]],
        "step": 3,
        "role": "police",
    }


def test_the_state_mapping_preserves_the_supplied_barrier_order() -> None:
    """`SealedState` already fixed the order, so the mapper must not re-sort."""
    wide = SealedState(
        config_sha256=Sha256Digest("0" * 64),
        self_pos=Position(1, 1),
        barriers=(Position(0, 9), Position(1, 0), Position(2, 5)),
        step=1,
        role=ActorRole.THIEF,
    )
    assert canonical_state_value(wide)["barriers"] == [[0, 9], [1, 0], [2, 5]]


@pytest.mark.parametrize("bad", [None, {"step": 1}, STATE.config_sha256, 1, "state"])
def test_only_an_exact_sealed_state_maps(bad: object) -> None:
    """No dict, no `LocalTruth`, no arbitrary object may stand in for the snapshot."""
    with pytest.raises(ValueError):
        canonical_state_value(bad)  # type: ignore[arg-type]
