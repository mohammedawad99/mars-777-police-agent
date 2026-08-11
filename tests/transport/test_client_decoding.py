"""The client validates what comes back as strictly as the server validates input.

A peer is untrusted in both directions. An operation that must complete with no
semantic value refuses one; `reveal` requires an exact `bool`, never `1` or
`"true"`; and the result digest must be a well-formed `Sha256Digest` before it
reaches the application.
"""

import asyncio

import pytest
from fastmcp import Client, FastMCP
from peer_ops import agreement, commitment

from mars777_police.app.protocol_errors import MalformedMessageError, StaleMessageError
from mars777_police.transport.client import PeerClient, envelope, wire_json
from mars777_police.transport.codec_final import encode_result_agreement
from mars777_police.transport.codec_turn import encode_commitment
from mars777_police.transport.wire_errors import TransportFailureError


class StubClient(PeerClient):
    """A `PeerClient` whose transport is replaced by a fixed answer."""

    def __init__(self, answer: object = None, failure: BaseException | None = None) -> None:
        super().__init__("http://127.0.0.1:1/mcp", timeout=1.0)
        self._answer = answer
        self._failure = failure

    async def call(self, tool: str, kind: str, payload: object) -> object:
        if self._failure is not None:
            raise self._failure
        return self._answer


def test_the_envelope_is_the_one_frozen_argument_shape() -> None:
    built = envelope("commitment", encode_commitment(commitment()))
    assert set(built) == {"request"}
    assert set(built["request"]) == {"kind", "payload"}
    assert built["request"]["kind"] == "commitment"


def test_wire_json_omits_absent_members_rather_than_emitting_null() -> None:
    from peer_ops import step0_exchange

    from mars777_police.transport.codec_declaration import encode_step0

    body = wire_json(encode_step0(step0_exchange(None)))
    hardware = body["declaration"]["teams"]["group_b"]["hardware"]
    assert "vram_gb" not in hardware
    assert body["declaration"]["times"].get("game_end") is None
    assert "game_end" not in body["declaration"]["times"]


def test_complete_accepts_only_an_absent_semantic_value() -> None:
    asyncio.run(StubClient(None).complete("negotiate", "step0", {}))
    for wrong in (True, False, "", 0, {"accepted": True}):
        with pytest.raises(MalformedMessageError):
            asyncio.run(StubClient(wrong).complete("negotiate", "step0", {}))


def test_legality_requires_an_exact_bool() -> None:
    assert asyncio.run(StubClient(True).legality(encode_commitment(commitment()))) is True
    assert asyncio.run(StubClient(False).legality(encode_commitment(commitment()))) is False
    for wrong in (1, 0, "true", "False", None, {"result": True}):
        with pytest.raises(MalformedMessageError):
            asyncio.run(StubClient(wrong).legality(encode_commitment(commitment())))


def test_digest_requires_a_well_formed_lowercase_hex_digest() -> None:
    request = encode_result_agreement(agreement())
    good = asyncio.run(StubClient("a" * 64).digest(request))
    assert good.value == "a" * 64
    for wrong in ("A" * 64, "a" * 63, "zz" + "a" * 62, "", None, 5, ["a" * 64]):
        with pytest.raises(MalformedMessageError):
            asyncio.run(StubClient(wrong).digest(request))


def test_a_remote_typed_failure_reaches_the_caller_unchanged() -> None:
    failure = StaleMessageError(StaleMessageError.error_id)
    with pytest.raises(StaleMessageError):
        asyncio.run(StubClient(failure=failure).complete("negotiate", "step0", {}))


def test_a_transport_failure_stays_a_transport_failure() -> None:
    failure = TransportFailureError(TransportFailureError.error_id)
    with pytest.raises(TransportFailureError):
        asyncio.run(StubClient(failure=failure).legality(encode_commitment(commitment())))


def test_the_client_exposes_its_endpoint_and_holds_no_game_state() -> None:
    client = PeerClient("http://127.0.0.1:9/mcp", timeout=3.0)
    assert client.url == "http://127.0.0.1:9/mcp"
    for absent in ("config", "cursor", "phase", "score", "truth"):
        assert not hasattr(client, absent)


def test_the_client_owns_its_own_session_and_shares_no_global_one() -> None:
    """The property, not the spelling: no module-level client, none shared.

    R17 asserted this by grepping for `async with Client(` in the source, which
    broke the moment the session moved behind a helper even though the property
    it cared about was untouched. This checks the property instead.
    """
    from mars777_police.transport import client as module

    assert not hasattr(module, "CLIENT")
    assert not any(isinstance(value, Client) for value in vars(module).values())
    first = PeerClient("http://127.0.0.1:9/mcp", timeout=1.0)
    second = PeerClient("http://127.0.0.1:8/mcp", timeout=1.0)
    assert first._session is None and second._session is None
    assert first.url != second.url
    assert isinstance(FastMCP, type)


def test_a_call_outside_a_held_session_still_opens_its_own() -> None:
    """A caller that manages no lifecycle keeps the original per-call behaviour."""
    client = PeerClient("http://127.0.0.1:9/mcp", timeout=0.5)
    assert client._session is None
    with pytest.raises(TransportFailureError):
        asyncio.run(client.complete("negotiate", "step0", {"a": 1}))
    assert client._session is None


def test_entering_a_dead_endpoint_is_a_transport_failure_not_a_peer_error() -> None:
    """Holding a session open cannot invent a peer failure when nobody answers."""

    async def hold() -> None:
        async with PeerClient("http://127.0.0.1:9/mcp", timeout=0.5):
            pass  # pragma: no cover - the entry above always raises here

    with pytest.raises(TransportFailureError):
        asyncio.run(hold())
