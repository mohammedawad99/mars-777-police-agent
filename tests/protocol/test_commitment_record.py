"""The exact eight-field sealed record builder (Stage 4E-R9-RESUME).

Eight keys, every one written out explicitly from an already-valid semantic
value, and no ninth key possible. The builder also enforces the two invariants
Stage 4E-R9-R1 froze - `state.step == cursor.step` and `state.role == role` -
**before** anything is hashed: a record that contradicts itself is a local
composition defect, not tampering, and hashing it would produce a digest nobody
could ever reproduce for the right reasons.

`cursor` is decomposed into the scalar `step` and `sub_game` and is never itself
serialized; the action fills `move` and never appears under an `action` key.
"""

import pytest

from mars777_police.app.protocol_values import NonceValue, Sha256Digest
from mars777_police.app.sealed_record_values import ActorRole, Intent, SealedState
from mars777_police.app.turn_cursor import TurnCursor
from mars777_police.domain.actions import MoveAction
from mars777_police.domain.board import Position
from mars777_police.domain.rules import Move
from mars777_police.protocol.commitment import build_sealed_record, canonical_state_value

STATE = SealedState(
    config_sha256=Sha256Digest("1" * 64),
    self_pos=Position(3, 4),
    barriers=(Position(0, 0), Position(2, 2)),
    step=3,
    role=ActorRole.POLICE,
)
CURSOR = TurnCursor(1, 3)


def record(**over: object) -> dict[str, object]:
    kwargs: dict[str, object] = {
        "state": STATE,
        "action": MoveAction(Move.N),
        "intent": Intent.LIE,
        "hint": "barrier",
        "cursor": CURSOR,
        "role": ActorRole.POLICE,
        "nonce": NonceValue("a" * 32),
    }
    return build_sealed_record(**(kwargs | over))  # type: ignore[arg-type]


def test_the_record_carries_exactly_the_eight_sealed_keys() -> None:
    assert set(record()) == {
        "state",
        "move",
        "intent",
        "hint",
        "step",
        "role",
        "sub_game",
        "nonce",
    }


ABSENT = ["cursor", "action", "h_commit", "phase", "timestamp", "game_id", "game_uid"]
ABSENT += ["accepted", "verified", "by_role", "verdict", "config_sha256", "self_pos"]


@pytest.mark.parametrize("absent", ABSENT)
def test_the_record_carries_no_ninth_key(absent: str) -> None:
    assert absent not in record()


def test_each_member_takes_its_value_from_the_intended_semantic_input() -> None:
    built = record()
    assert built["state"] == canonical_state_value(STATE)
    assert built["move"] == {"kind": "MOVE", "value": "N"}
    assert built["intent"] == "lie"
    assert built["hint"] == "barrier"
    assert built["step"] == CURSOR.step == 3
    assert built["role"] == "police"
    assert built["sub_game"] == CURSOR.sub_game == 1
    assert built["nonce"] == "a" * 32


def test_the_free_text_hint_is_nfc_normalised_into_the_record() -> None:
    assert record(hint="e\u0301")["hint"] == "\u00e9"


def test_the_builder_does_not_mutate_its_semantic_inputs_or_cache() -> None:
    before = (STATE.barriers, STATE.step, STATE.role)
    first, second = record(), record()
    assert first == second and first is not second
    assert (STATE.barriers, STATE.step, STATE.role) == before
    assert first["state"] is not second["state"]


BAD = {
    "state": [None, {"step": 3}, "state", 3],
    "action": ["N", Move.N, None, 0],
    "intent": ["lie", "LIE", None, True],
    "hint": [None, 1, b"hint", ["hint"]],
    "cursor": [(1, 3), None, 3, {"step": 3}],
    "role": ["police", "POLICE", None, 0],
    "nonce": ["a" * 32, None, True, Sha256Digest("0" * 64)],
}


@pytest.mark.parametrize(("field", "bad"), [(f, b) for f, vals in BAD.items() for b in vals])
def test_an_input_of_the_wrong_exact_type_is_refused_never_coerced(field: str, bad: object) -> None:
    """A raw string, dict or tuple never stands in for an already-valid value."""
    with pytest.raises(ValueError):
        record(**{field: bad})


def test_subclasses_of_the_composed_inputs_are_refused() -> None:
    class LooseDigest(Sha256Digest): ...

    class LooseMove(MoveAction): ...

    with pytest.raises(ValueError):
        record(action=LooseMove(Move.N))
    with pytest.raises(ValueError):
        canonical_state_value(LooseDigest("0" * 64))
