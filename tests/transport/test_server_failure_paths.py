"""Every tool translates a failure, and the codec refuses an unknown token.

The four `except` arms are not decoration: a failure escaping any one of them
would reach the peer as a framework error carrying our internals, which is what
the masking rule exists to prevent.
"""

import asyncio

import pytest
from fastmcp import Client
from fastmcp.exceptions import ToolError
from peer_ops import (
    RecordingOperations,
    agreement,
    audit_document,
    final_nonce,
    proposal,
    step0_exchange,
)

from mars777_police.app.protocol_errors import (
    AuthFailureError,
    LocalDefectError,
    MalformedMessageError,
    StaleMessageError,
)
from mars777_police.transport.client import wire_json
from mars777_police.transport.codec_declaration import encode_step0
from mars777_police.transport.codec_final import encode_final_nonce, encode_result_agreement
from mars777_police.transport.codec_pregame import encode_proposal
from mars777_police.transport.codec_turn import decode_action
from mars777_police.transport.wire_turn import MoveActionWire


def failing_call(tool: str, kind: str, payload: object, failure: BaseException) -> str:
    operations = RecordingOperations()
    operations.failure = failure
    body = wire_json(payload) if hasattr(payload, "model_dump") else payload

    async def run() -> str:
        from mars777_police.transport.server import build_server

        async with Client(build_server(operations)) as client:
            with pytest.raises(ToolError) as raised:
                await client.call_tool(tool, {"request": {"kind": kind, "payload": body}})
            return str(raised.value)

    return asyncio.run(run())


@pytest.mark.parametrize(
    ("tool", "kind", "payload"),
    [
        ("negotiate", "step0", encode_step0(step0_exchange())),
        ("negotiate", "config_proposal", encode_proposal(proposal())),
        ("submit_audit", "final_nonce_reveal", encode_final_nonce(final_nonce())),
        ("submit_audit", "audit_disclosure", audit_document()),
        ("receive_control", "result_agreement", encode_result_agreement(agreement())),
    ],
)
def test_every_tool_preserves_a_known_failure_identity(
    tool: str, kind: str, payload: object
) -> None:
    assert failing_call(tool, kind, payload, StaleMessageError("x")) == StaleMessageError.error_id


@pytest.mark.parametrize(
    ("tool", "kind", "payload"),
    [
        ("negotiate", "step0", encode_step0(step0_exchange())),
        ("submit_audit", "audit_disclosure", audit_document()),
        ("receive_control", "result_agreement", encode_result_agreement(agreement())),
    ],
)
def test_every_tool_masks_an_unknown_failure(tool: str, kind: str, payload: object) -> None:
    message = failing_call(tool, kind, payload, RuntimeError("secret=abc /home/x.py:3"))
    assert message == LocalDefectError.error_id
    assert "secret" not in message and "x.py" not in message


def test_an_auth_failure_keeps_its_own_identity() -> None:
    assert (
        failing_call("negotiate", "step0", encode_step0(step0_exchange()), AuthFailureError("x"))
        == AuthFailureError.error_id
    )


def test_an_unknown_move_token_is_malformed_not_a_domain_guess() -> None:
    """The protocol layer maps the vocabulary; the domain never guesses."""
    with pytest.raises(MalformedMessageError):
        decode_action(MoveActionWire(kind="MOVE", value="NORTHWEST"))
    with pytest.raises(MalformedMessageError):
        decode_action(MoveActionWire(kind="MOVE", value="n"))
