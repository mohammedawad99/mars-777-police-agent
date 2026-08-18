"""The outbound KIT boundary: which tool, which argument name, which bytes.

Every expectation is a **complete** structure rather than a subset, because a
partial assertion cannot catch the failure this stage exists to prevent - a
message that carries every value the test looked at and one the peer needs and
never receives.

The argument-name asymmetry is asserted on its own: `submit_audit` takes
`payload` and the other three take `message`, and a peer that sends `message`
to `submit_audit` gets a schema error at the one moment both sides are trying
to agree a result.
"""

import pytest
from kit_builders import (
    COMMIT,
    NONCE,
    PEER_GROUP,
    TERMS,
    kit_audit,
    kit_claim,
    kit_control,
    kit_greeting,
    kit_response,
    kit_turn,
)
from kit_wire_vectors import ARGUMENT_NAMES, TURN
from peer_ops import commitment

from mars777_police.app.kit_messages import KitRole
from mars777_police.transport.call_arguments import kit_call, strict_arguments
from mars777_police.transport.codec_turn import encode_commitment


def test_a_turn_renders_the_full_pinned_ten_key_shape_with_nulls_explicit() -> None:
    tool, arguments = kit_call(kit_turn())

    assert tool == "receive_turn"
    assert arguments == {"message": TURN}


def test_the_optional_turn_members_render_in_the_kit_spelling() -> None:
    tool, arguments = kit_call(
        kit_turn(
            barrier_placed=None,
            capture_claim=kit_claim(),
            claim_response=kit_response(),
            survival_claimed=True,
        )
    )
    message = arguments["message"]

    assert tool == "receive_turn"
    assert message["barrier_placed"] is None
    assert message["capture_claim"] == [2, 4]
    assert message["claim_response"] == {"claim": [2, 4], "caught": False}
    assert message["win_claim"] == {"type": "survival"}


def test_an_audit_is_the_one_call_whose_argument_is_named_payload() -> None:
    tool, arguments = kit_call(kit_audit())

    assert tool == "submit_audit"
    assert arguments == {
        "payload": {
            "sender": "police",
            "records": [
                {
                    "payload": {"step": 1, "move": "MOVE:N"},
                    "nonce": "0" * 32,
                    "commit": COMMIT.value,
                }
            ],
            "result_claim": "capture",
        }
    }


def test_a_control_message_renders_its_complete_pinned_shape() -> None:
    tool, arguments = kit_call(kit_control())

    assert tool == "receive_control"
    assert arguments == {
        "message": {
            "kind": "status",
            "sender": "police",
            "sub_game_number": 1,
            "status": "ready",
            "step_budget": 0.0,
            "payload": None,
        }
    }


def test_a_greeting_omits_every_absent_member_rather_than_sending_null() -> None:
    tool, arguments = kit_call(kit_greeting())

    assert tool == "negotiate"
    assert arguments == {
        "message": {
            "terms": TERMS,
            "nonce": NONCE,
            "signature": "b" * 64,
            "group_id": PEER_GROUP,
            "role": "police",
            "sub_game_number": 1,
        }
    }


@pytest.mark.parametrize(
    ("builder", "tool"),
    [
        (kit_greeting, "negotiate"),
        (kit_turn, "receive_turn"),
        (kit_audit, "submit_audit"),
        (kit_control, "receive_control"),
    ],
)
def test_each_message_type_selects_its_own_tool_and_argument_name(builder, tool) -> None:
    name, arguments = kit_call(builder())

    assert name == tool
    assert list(arguments) == [ARGUMENT_NAMES[tool]]


def test_the_strict_arguments_are_byte_identical_to_the_frozen_envelope() -> None:
    """KIT support may not move one byte of what the internal wire already sends."""
    assert strict_arguments("commitment", encode_commitment(commitment())) == {
        "request": {
            "kind": "commitment",
            "payload": {
                "cursor": {"sub_game": 1, "step": 1},
                "h_commit": commitment().h_commit.value,
            },
        }
    }


def test_no_invented_peer_token_reaches_the_wire() -> None:
    """`KIT_CORE_V1` is our local selection name; the pinned kit defines no such token."""
    rendered = repr([kit_call(builder())[1] for builder in (kit_greeting, kit_turn, kit_audit)])

    assert "KIT_CORE_V1" not in rendered
    assert "STRICT_PROJECT" not in rendered


def test_the_sender_is_the_kit_spelling_of_a_role_and_nothing_else() -> None:
    assert [one.value for one in KitRole] == ["police", "thief"]
