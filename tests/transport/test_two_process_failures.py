"""Typed failure propagation and the result cadence, across real processes.

A remote failure must arrive at the caller as the **same typed failure** it
would have raised locally, carrying no traceback - and an unreachable endpoint
must be a transport failure rather than a protocol accusation.
"""

import asyncio

import pytest
from peer_ops import agreement
from peer_process import PeerProcess, free_port
from r16_builders import GROUP_A

from mars777_police.app.peer_supervision import PeerDeadline, TimeoutPolicy
from mars777_police.app.protocol_errors import MalformedMessageError
from mars777_police.transport.client import PeerClient
from mars777_police.transport.codec_final import encode_result_agreement
from mars777_police.transport.wire_errors import TransportFailureError

TIMEOUT = 20.0


@pytest.fixture(scope="module")
def peer() -> object:
    """One peer process for the module, always torn down."""
    with PeerProcess(GROUP_A) as process:
        yield process


def test_an_unknown_kind_is_refused_as_malformed(peer: object) -> None:
    client = PeerClient(peer.url, PeerDeadline(TimeoutPolicy(TIMEOUT)))
    with pytest.raises(MalformedMessageError):
        asyncio.run(client.call("negotiate", "not_a_kind", {}))


def test_a_valid_kind_on_the_wrong_tool_is_refused(peer: object) -> None:
    """No cross-tool redispatch, proved over the real transport."""
    client = PeerClient(peer.url, PeerDeadline(TimeoutPolicy(TIMEOUT)))
    with pytest.raises(MalformedMessageError):
        asyncio.run(client.call("receive_turn", "step0", {}))


def test_a_wrongly_typed_payload_is_refused(peer: object) -> None:
    client = PeerClient(peer.url, PeerDeadline(TimeoutPolicy(TIMEOUT)))
    with pytest.raises(MalformedMessageError):
        asyncio.run(client.call("receive_control", "result_agreement", {"game_id": 5}))


def test_an_unreachable_endpoint_is_a_transport_failure(peer: object) -> None:
    """Nobody answered, so nothing may be concluded about the protocol."""
    client = PeerClient(f"http://127.0.0.1:{free_port()}/mcp", PeerDeadline(TimeoutPolicy(2.0)))
    with pytest.raises(TransportFailureError) as raised:
        asyncio.run(client.call("negotiate", "step0", {}))
    assert raised.value.error_id == "E-TRANSPORT"


def test_no_remote_failure_leaks_a_traceback(peer: object) -> None:
    client = PeerClient(peer.url, PeerDeadline(TimeoutPolicy(TIMEOUT)))
    with pytest.raises(MalformedMessageError) as raised:
        asyncio.run(client.call("negotiate", "not_a_kind", {}))
    for leak in ("Traceback", 'File "', "line ", "pydantic"):
        assert leak not in str(raised.value)


def test_the_result_digest_round_trips_across_the_process_boundary(peer: object) -> None:
    client = PeerClient(peer.url, PeerDeadline(TimeoutPolicy(TIMEOUT)))
    digest = asyncio.run(client.digest(encode_result_agreement(agreement())))
    assert len(digest.value) == 64
    second = asyncio.run(client.digest(encode_result_agreement(agreement())))
    assert second == digest


def test_the_same_semantic_request_is_re_sendable_unchanged(peer: object) -> None:
    """A retry re-sends the identical value; nothing is regenerated."""
    request = encode_result_agreement(agreement())
    client = PeerClient(peer.url, PeerDeadline(TimeoutPolicy(TIMEOUT)))
    first = asyncio.run(client.digest(request))
    assert asyncio.run(client.digest(request)) == first
    assert request.timestamp == encode_result_agreement(agreement()).timestamp
