"""The full two-request cadence, driven by the **production** workflow.

No test here compares a digest or computes one. Our peer owns a real
`ResultExchange`: it receives the proposer's request through the same production
entry point its server would use, then sends its own through
`PeerTransportPort`, and production verifies the digest that comes back.

The opponent is a genuinely separate OS process reachable only over FastMCP
Streamable HTTP, running the same production workflow on its side.
"""

import asyncio
import json
from pathlib import Path

import pytest
from cadence_ops import CadenceOperations, exchange_for
from peer_process import CadencePeer
from r16_builders import GROUP_A, GROUP_B, STAMP

from mars777_police.app.peer_supervision import PeerDeadline, TimeoutPolicy
from mars777_police.transport.client import PeerClient
from mars777_police.transport.peer_transport import FastMcpPeerTransport
from mars777_police.transport.server import PEER_TOOLS

TIMEOUT = 20.0


def status_of(path: Path) -> dict[str, object]:
    """Read the opponent process's self-reported verdict."""
    return json.loads(path.read_text(encoding="utf-8"))


def transport_to(url: str) -> FastMcpPeerTransport:
    """The concrete adapter, injected where the port is expected."""
    return FastMcpPeerTransport(PeerClient(url, PeerDeadline(TimeoutPolicy(TIMEOUT))))


@pytest.fixture
def opponent(tmp_path: Path) -> object:
    """The proposer, in its own process, always torn down."""
    with CadencePeer(GROUP_B, tmp_path / "p.json", base=100) as peer:
        yield peer


def our_peer(url: str) -> object:
    """Our non-proposer half, wired to the opponent through the port."""
    exchange = exchange_for(GROUP_A, 200)
    exchange.transport = transport_to(url)
    return exchange


def proposers_request(url: str) -> object:
    """The request the opponent proposed, as our server would receive it."""
    remote = exchange_for(GROUP_B, 100)
    remote.transport = transport_to(url)
    return remote.runtime.open_agreement(remote.own)


def test_the_full_cadence_completes_through_the_production_workflow(
    opponent: object,
) -> None:
    """Both directions, both digests, one production comparison - no test math."""
    us = our_peer(opponent.url)
    assert not us.runtime.is_proposer
    assert status_of(opponent.status)["is_proposer"] is True

    first = proposers_request(opponent.url)
    assert first.timestamp == STAMP

    ours = us.accept_peer_request(first, GROUP_B)
    assert us.peer_request_handled
    assert us.local_digest == ours
    assert us.timestamp == STAMP

    asyncio.run(us.send_response(us.timestamp))

    assert us.own_request_sent
    assert us.peer_digest == us.local_digest
    assert us.verified
    assert us.gate.is_agreed
    assert us.is_agreed

    remote = status_of(opponent.status)
    assert remote["peer_request_handled"] is True
    assert remote["timestamp"] == STAMP.value
    assert remote["local_digest"] == us.local_digest.value

    # The opponent process answers requests but never receives a digest back in
    # this harness, so it holds no peer digest and production correctly refuses
    # to call it complete. That is the both-directions rule holding, not a
    # defect: answering is insufficient on its own.
    assert remote["peer_digest"] is None
    assert remote["verified"] is False
    assert remote["is_agreed"] is False


def test_the_second_request_echoes_the_proposed_timestamp(opponent: object) -> None:
    us = our_peer(opponent.url)
    first = proposers_request(opponent.url)
    us.accept_peer_request(first, GROUP_B)
    asyncio.run(us.send_response(us.timestamp))
    assert us.timestamp == first.timestamp == STAMP
    assert status_of(opponent.status)["timestamp"] == STAMP.value


def test_the_cadence_added_no_fifth_public_tool(opponent: object) -> None:
    from fastmcp import Client
    from fastmcp.client.transports import StreamableHttpTransport

    async def run() -> list[str]:
        async with Client(StreamableHttpTransport(opponent.url), timeout=TIMEOUT) as client:
            return sorted(tool.name for tool in await client.list_tools())

    assert asyncio.run(run()) == sorted(PEER_TOOLS)
    assert CadenceOperations is not None
