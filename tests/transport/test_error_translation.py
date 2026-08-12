"""Failures keep their identity, or reveal nothing - and never become `False`.

The rule that carries the most weight: a transport, parse, authentication or
protocol failure must never arrive as `reveal`'s legality `False`. If it could,
an unreachable peer would look exactly like an illegal move.
"""

import asyncio

import pytest
from fastmcp import Client
from fastmcp.exceptions import ToolError
from peer_ops import ILLEGAL_HINT, commitment, reveal
from peer_recorder import RecordingOperations

from mars777_police.app.protocol_errors import (
    AuthFailureError,
    ConfigMismatchError,
    LocalDefectError,
    MalformedMessageError,
    ReportDisagreeError,
    StaleMessageError,
)
from mars777_police.transport.client import wire_json
from mars777_police.transport.codec_turn import encode_commitment, encode_reveal
from mars777_police.transport.server import build_server
from mars777_police.transport.wire_errors import TransportFailureError, inbound, outbound

IDENTITIES = [
    StaleMessageError,
    AuthFailureError,
    ConfigMismatchError,
    ReportDisagreeError,
    MalformedMessageError,
    LocalDefectError,
]


def call_with(failure: BaseException | None, payload: object, kind: str = "commitment") -> object:
    operations = RecordingOperations()
    operations.failure = failure

    async def run() -> object:
        async with Client(build_server(operations)) as client:
            body = wire_json(payload) if hasattr(payload, "model_dump") else payload
            return (
                await client.call_tool("receive_turn", {"request": {"kind": kind, "payload": body}})
            ).data

    return asyncio.run(run())


@pytest.mark.parametrize("error", IDENTITIES, ids=lambda e: e.error_id)
def test_a_known_failure_crosses_with_exactly_its_identity(error: type) -> None:
    with pytest.raises(ToolError) as raised:
        call_with(error(error.error_id), encode_commitment(commitment()))
    assert str(raised.value) == error.error_id


@pytest.mark.parametrize("error", IDENTITIES, ids=lambda e: e.error_id)
def test_the_client_rebuilds_the_same_typed_failure(error: type) -> None:
    rebuilt = inbound(error.error_id)
    assert type(rebuilt) is error
    assert rebuilt.error_id == error.error_id


def test_an_unknown_failure_masks_its_internals_completely() -> None:
    """A defect on our side must not narrate itself to an untrusted peer."""
    secret = RuntimeError("key=deadbeef at /home/awad/secret.py line 42")
    with pytest.raises(ToolError) as raised:
        call_with(secret, encode_commitment(commitment()))
    message = str(raised.value)
    assert message == LocalDefectError.error_id
    for leak in ("deadbeef", "secret.py", "RuntimeError", "Traceback", "line 42"):
        assert leak not in message


def test_outbound_never_reveals_an_exception_message() -> None:
    assert str(outbound(RuntimeError("boom /etc/passwd"))) == LocalDefectError.error_id
    assert str(outbound(StaleMessageError("anything at all"))) == StaleMessageError.error_id


def test_an_unknown_remote_identity_is_malformed_not_guessed() -> None:
    for text in ("E-NOT-A-REAL-ID", "", "ValueError: boom", "E-PROTO-STALE "):
        assert type(inbound(text)) is MalformedMessageError


def test_transport_failure_is_a_separate_identity_from_every_protocol_outcome() -> None:
    """A peer that never answered has told us nothing about the protocol."""
    from mars777_police.app.protocol_errors import PeerProtocolError

    assert TransportFailureError.error_id == "E-TRANSPORT"
    assert not issubclass(TransportFailureError, PeerProtocolError)


def test_no_failure_ever_arrives_as_a_legality_false() -> None:
    assert call_with(None, encode_reveal(reveal()), "reveal").accepted is True
    assert call_with(None, encode_reveal(reveal(ILLEGAL_HINT)), "reveal").accepted is False
    for error in IDENTITIES:
        with pytest.raises(ToolError):
            call_with(error(error.error_id), encode_reveal(reveal()), "reveal")


def test_no_new_error_identity_was_introduced() -> None:
    from mars777_police.transport.wire_errors import _BY_IDENTITY

    assert set(_BY_IDENTITY) == {error.error_id for error in IDENTITIES} | {
        "E-NET-CONVENTION-MISMATCH"
    }
