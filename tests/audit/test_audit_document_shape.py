"""Every refusal branch of the untrusted-document reader.

A hostile or broken document is a **transport-shaped** failure -
`E-PROTO-MALFORMED` - not a tampering verdict. Collapsing the two would let a
truncated payload look like an accusation.
"""

import pytest
from audit_builders import PEER_GROUP, document, entry, nonce_batch, runtime

from mars777_police.app.audit_disclosure import turns
from mars777_police.app.protocol_errors import MalformedMessageError
from mars777_police.domain.actions import BarrierAction, MoveAction
from mars777_police.domain.board import Position
from mars777_police.domain.rules import Move


def refuse(**overrides: object) -> MalformedMessageError:
    """Drive a broken document through the runtime and return the refusal."""
    live = runtime()
    live.accept_final_nonce_reveal(nonce_batch(), PEER_GROUP)
    doc = document()
    doc.update(overrides)
    with pytest.raises(MalformedMessageError) as raised:
        live.accept_audit_disclosure(doc)
    return raised.value


def broken_entry(**entry_overrides: object) -> MalformedMessageError:
    first = entry(1)
    first.update(entry_overrides)
    return refuse(entries=[first, entry(2)])


def test_an_entry_that_is_not_an_object_is_refused() -> None:
    assert refuse(entries=["not an object"]).error_id == "E-PROTO-MALFORMED"


def test_an_entry_missing_a_text_member_is_refused() -> None:
    first = entry(1)
    del first["role"]
    assert refuse(entries=[first]).error_id == "E-PROTO-MALFORMED"


def test_an_entry_with_a_non_integer_step_is_refused() -> None:
    assert broken_entry(step="one").error_id == "E-PROTO-MALFORMED"


def test_an_entry_state_that_is_not_an_object_is_refused() -> None:
    assert broken_entry(state="not an object").error_id == "E-PROTO-MALFORMED"


@pytest.mark.parametrize("bad", [[1, 2, 3], "somewhere", [1, "two"]])
def test_a_malformed_position_is_refused(bad: object) -> None:
    first = entry(1)
    first["state"] = dict(first["state"], self_pos=bad)  # type: ignore[arg-type]
    assert refuse(entries=[first, entry(2)]).error_id == "E-PROTO-MALFORMED"


def test_a_malformed_barrier_list_is_refused() -> None:
    first = entry(1)
    first["state"] = dict(first["state"], barriers="none")  # type: ignore[arg-type]
    assert refuse(entries=[first, entry(2)]).error_id == "E-PROTO-MALFORMED"


def test_a_malformed_barrier_entry_is_refused() -> None:
    first = entry(1)
    first["state"] = dict(first["state"], barriers=[[1]])  # type: ignore[arg-type]
    assert refuse(entries=[first, entry(2)]).error_id == "E-PROTO-MALFORMED"


@pytest.mark.parametrize(
    "bad",
    [
        "not an object",
        {"kind": "MOVE"},
        {"kind": "MOVE", "value": "N", "extra": 1},
        {"kind": "MOVE", "value": 7},
        {"kind": "MOVE", "value": "NORTH"},
        {"kind": "BARRIER", "value": [1]},
        {"kind": "TELEPORT", "value": "N"},
    ],
)
def test_a_move_that_is_not_a_known_action_is_refused(bad: object) -> None:
    """Fail-closed: no default to STAY, no normalisation, no dropped cell."""
    assert broken_entry(move=bad).error_id == "E-PROTO-MALFORMED"


def test_a_disclosed_move_becomes_a_domain_action() -> None:
    """The internal parsed value is semantic, and a barrier keeps its exact cell."""
    doc = document()
    doc["entries"][0]["move"] = {"kind": "BARRIER", "value": [4, 5]}  # type: ignore[index]
    parsed = turns(doc)
    assert parsed[0].move == BarrierAction(Position(4, 5))
    assert parsed[1].move == MoveAction(Move.N)
    assert parsed[0].self_pos == Position(2, 3)


def test_a_missing_identity_member_is_refused() -> None:
    live = runtime()
    live.accept_final_nonce_reveal(nonce_batch(), PEER_GROUP)
    doc = document()
    del doc["config_sha256"]
    with pytest.raises(MalformedMessageError):
        live.accept_audit_disclosure(doc)
