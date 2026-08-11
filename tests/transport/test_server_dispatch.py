"""Routing: the right handler, the right semantic value, the right result.

Dispatch is by explicit `kind`. These tests assert what the **application**
received, not merely that the call returned - a router that accepted everything
and decoded the wrong family would pass the schema tests and fail here.
"""

import asyncio

import pytest
from fastmcp import Client
from peer_ops import (
    ILLEGAL_HINT,
    RESULT_DIGEST,
    acknowledgement,
    agreement,
    audit_document,
    commitment,
    final_nonce,
    lock_evidence,
    proposal,
    reveal,
    step0_exchange,
)
from peer_recorder import RecordingOperations

from mars777_police.transport.client import wire_json
from mars777_police.transport.codec_declaration import encode_step0
from mars777_police.transport.codec_final import encode_final_nonce, encode_result_agreement
from mars777_police.transport.codec_pregame import encode_lock, encode_proposal
from mars777_police.transport.codec_turn import (
    encode_acknowledgement,
    encode_commitment,
    encode_reveal,
)
from mars777_police.transport.server import build_server


def invoke(tool: str, kind: str, payload: object) -> tuple[object, RecordingOperations]:
    operations = RecordingOperations()
    body = wire_json(payload) if hasattr(payload, "model_dump") else payload

    async def run() -> object:
        async with Client(build_server(operations)) as client:
            result = await client.call_tool(tool, {"request": {"kind": kind, "payload": body}})
            return result.data

    return asyncio.run(run()), operations


@pytest.mark.parametrize(
    ("tool", "kind", "payload"),
    [
        ("negotiate", "step0", encode_step0(step0_exchange())),
        ("negotiate", "config_proposal", encode_proposal(proposal())),
        ("negotiate", "config_lock", encode_lock(lock_evidence())),
        ("receive_turn", "commitment", encode_commitment(commitment())),
        ("receive_turn", "acknowledgement", encode_acknowledgement(acknowledgement())),
        ("submit_audit", "final_nonce_reveal", encode_final_nonce(final_nonce())),
        ("submit_audit", "audit_disclosure", audit_document()),
    ],
)
def test_ordinary_completion_carries_no_semantic_value(
    tool: str, kind: str, payload: object
) -> None:
    data, operations = invoke(tool, kind, payload)
    assert data is None
    assert operations.kinds() == [kind]


def test_each_kind_reaches_its_own_handler_with_the_right_value() -> None:
    _, operations = invoke("negotiate", "step0", encode_step0(step0_exchange()))
    name, value = operations.seen[0]
    assert name == "step0"
    assert value == step0_exchange()


def test_reveal_returns_the_legality_bool_in_both_directions() -> None:
    legal, operations = invoke("receive_turn", "reveal", encode_reveal(reveal()))
    assert legal is True
    assert operations.kinds() == ["reveal"]
    illegal, _ = invoke("receive_turn", "reveal", encode_reveal(reveal(ILLEGAL_HINT)))
    assert illegal is False


def test_result_agreement_returns_the_digest_as_lowercase_hex() -> None:
    data, operations = invoke(
        "receive_control", "result_agreement", encode_result_agreement(agreement())
    )
    assert data == RESULT_DIGEST.value
    assert len(str(data)) == 64
    assert operations.kinds() == ["result_agreement"]


def test_the_audit_document_reaches_the_handler_json_native() -> None:
    _, operations = invoke("submit_audit", "audit_disclosure", audit_document())
    _, value = operations.seen[0]
    assert value == audit_document()
    assert isinstance(value, dict)


def test_the_router_holds_no_state_between_calls() -> None:
    _, first = invoke("receive_turn", "commitment", encode_commitment(commitment()))
    _, second = invoke("receive_turn", "commitment", encode_commitment(commitment()))
    assert first.kinds() == second.kinds() == ["commitment"]
