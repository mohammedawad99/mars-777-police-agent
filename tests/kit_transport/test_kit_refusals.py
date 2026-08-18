"""What the KIT profile refuses, and the one live outbound proof.

Two halves of the same rule. A message that does not conform is refused at the
boundary and reaches no runtime - decided before any state change, because an
inbound message is adversarial input and a partly applied bad one cannot be
rolled back. And a process that never registered the KIT surface cannot put a
KIT message on the wire at all: the arguments are refused where they are built.

The outbound half runs against a real KIT ingress over HTTP, so what is proved
is a round trip through the production client, the production registration and
the production router - not a helper calling a codec.
"""

import asyncio

import pytest
from fastmcp.exceptions import ToolError
from kit_builders import kit_control, kit_turn
from kit_session_support import OUR_GROUP, KitLiveServer, kit_context
from kit_wire_vectors import AUDIT, CONTROL, NEGOTIATION
from peer_recorder import RecordingOperations

from mars777_police.app.peer_supervision import PeerDeadline, TimeoutPolicy
from mars777_police.app.protocol_errors import LocalDefectError
from mars777_police.app.protocol_values import Sha256Digest
from mars777_police.transport.client import PeerClient
from mars777_police.transport.peer_transport import FastMcpPeerTransport
from mars777_police.transport.server import build_server
from mars777_police.transport.transport_profiles import TransportEnvelopeProfile

TIMEOUT = 15.0


def call(tool: str, argument: dict[str, object]) -> RecordingOperations:
    """One call against a live KIT peer, through the production surface."""
    operations = RecordingOperations()

    async def run(url: str) -> None:
        from fastmcp import Client

        async with Client(url) as client:
            await client.call_tool(tool, argument)

    with KitLiveServer(operations, kit_context()) as peer:
        asyncio.run(run(peer.url))
    return operations


def test_a_greeting_whose_terms_disagree_is_refused_on_the_record() -> None:
    """A constitution disagreement, not a wire fault - and never repaired."""
    with pytest.raises(ToolError, match="E-CONFIG-MISMATCH"):
        call("negotiate", {"message": NEGOTIATION})


def test_an_audit_outside_the_pinned_shape_is_refused() -> None:
    with pytest.raises(ToolError, match="E-PROTO-MALFORMED"):
        call("submit_audit", {"payload": AUDIT | {"result_claim": "победа"}})


def test_a_control_command_outside_the_pinned_vocabulary_is_refused() -> None:
    with pytest.raises(ToolError, match="E-PROTO-MALFORMED"):
        call("receive_control", {"message": CONTROL | {"kind": "shutdown"}})


def test_a_conformant_control_signal_is_honoured_and_settles_nothing() -> None:
    operations = RecordingOperations()
    context = kit_context()

    async def run(url: str) -> None:
        from fastmcp import Client

        async with Client(url) as client:
            await client.call_tool("receive_control", {"message": CONTROL})

    with KitLiveServer(operations, context) as peer:
        asyncio.run(run(peer.url))

    assert context.last_control is not None
    assert operations.seen == []


def test_a_kit_ingress_without_its_out_of_band_context_refuses_to_be_built() -> None:
    """It would have to invent a sub-game number, and that aggregates two games."""
    with pytest.raises(LocalDefectError):
        build_server(RecordingOperations(), profile=TransportEnvelopeProfile.KIT_EXTERNAL)


def test_our_own_client_reaches_a_kit_ingress_over_real_http() -> None:
    """The outbound half: our encoder, our client, a real KIT surface, one session."""
    operations = RecordingOperations()

    async def run(url: str) -> None:
        client = PeerClient(
            url, PeerDeadline(TimeoutPolicy(TIMEOUT)), TransportEnvelopeProfile.KIT_EXTERNAL
        )
        async with client:
            transport = FastMcpPeerTransport(client)
            await transport.send_kit(kit_turn())
            await transport.send_kit(kit_control())

    with KitLiveServer(operations, kit_context()) as peer:
        asyncio.run(run(peer.url))

    assert operations.kinds() == ["commitment"]
    value = operations.seen[0][1]
    assert value.cursor.step == 7
    assert value.h_commit == Sha256Digest("a" * 64)
    assert OUR_GROUP == "MaRs-777"
