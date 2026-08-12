"""All four tool surfaces, across two genuinely independent OS processes.

Two `subprocess` peers, each with its own memory, its own application runtime
and its own port, reachable only over Streamable HTTP. No shared object, no
shared singleton, no queue carrying Python values - if the transport were
subtly broken, nothing here could paper over it.

Ports are OS-assigned, readiness is polled against the real endpoint, and both
processes are terminated even when a test fails.
"""

import asyncio

import pytest
from peer_ops import (
    ILLEGAL_HINT,
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
from peer_process import PeerProcess
from r16_builders import GROUP_A, GROUP_B

from mars777_police.transport.client import PeerClient
from mars777_police.transport.codec_declaration import encode_step0
from mars777_police.transport.codec_final import encode_final_nonce, encode_result_agreement
from mars777_police.transport.codec_pregame import encode_lock, encode_proposal
from mars777_police.transport.codec_turn import (
    encode_acknowledgement,
    encode_commitment,
    encode_reveal,
)
from mars777_police.transport.server import PEER_TOOLS

TIMEOUT = 20.0


@pytest.fixture(scope="module")
def peers() -> object:
    """Both peers, started once for the module and always torn down."""
    with PeerProcess(GROUP_A) as police, PeerProcess(GROUP_B) as thief:
        yield police, thief


def test_the_two_peers_listen_on_distinct_endpoints(peers: object) -> None:
    police, thief = peers
    assert police.url != thief.url
    assert police.port != thief.port
    assert police.url.startswith("http://127.0.0.1:")


def test_tool_discovery_exposes_exactly_four_peer_tools(peers: object) -> None:
    from fastmcp import Client
    from fastmcp.client.transports import StreamableHttpTransport

    police, _ = peers

    async def run() -> list[str]:
        async with Client(StreamableHttpTransport(police.url), timeout=TIMEOUT) as client:
            return sorted(tool.name for tool in await client.list_tools())

    assert asyncio.run(run()) == sorted(PEER_TOOLS)


def call(url: str, tool: str, kind: str, payload: object) -> object:
    client = PeerClient(url, timeout=TIMEOUT)
    return asyncio.run(client.call(tool, kind, payload))


@pytest.mark.parametrize("vram", [None, 24], ids=["cpu-only", "gpu"])
def test_step0_crosses_the_transport_on_both_hardware_branches(
    peers: object, vram: int | None
) -> None:
    police, _ = peers
    assert call(police.url, "negotiate", "step0", encode_step0(step0_exchange(vram))) is None


def test_config_proposal_and_lock_cross_the_transport(peers: object) -> None:
    police, _ = peers
    assert call(police.url, "negotiate", "config_proposal", encode_proposal(proposal())) is None
    assert call(police.url, "negotiate", "config_lock", encode_lock(lock_evidence())) is None


def test_the_full_turn_exchange_crosses_the_transport(peers: object) -> None:
    police, _ = peers
    url = police.url
    assert call(url, "receive_turn", "commitment", encode_commitment(commitment())) is None
    assert (
        call(url, "receive_turn", "acknowledgement", encode_acknowledgement(acknowledgement()))
        is None
    )


def test_a_legal_reveal_returns_true_across_two_processes(peers: object) -> None:
    police, _ = peers
    client = PeerClient(police.url, timeout=TIMEOUT)
    assert asyncio.run(client.outcome(encode_reveal(reveal()))).accepted is True


def test_an_illegal_reveal_returns_false_across_two_processes(peers: object) -> None:
    police, _ = peers
    client = PeerClient(police.url, timeout=TIMEOUT)
    assert asyncio.run(client.outcome(encode_reveal(reveal(ILLEGAL_HINT)))).accepted is False


def test_the_audit_surfaces_cross_the_transport(peers: object) -> None:
    police, _ = peers
    url = police.url
    assert (
        call(url, "submit_audit", "final_nonce_reveal", encode_final_nonce(final_nonce())) is None
    )
    assert call(url, "submit_audit", "audit_disclosure", audit_document()) is None


def test_result_agreement_returns_a_digest_across_two_processes(peers: object) -> None:
    police, _ = peers
    client = PeerClient(police.url, timeout=TIMEOUT)
    digest = asyncio.run(client.digest(encode_result_agreement(agreement())))
    assert len(digest.value) == 64
    assert digest.value == digest.value.lower()


def test_both_peers_serve_the_same_surface_independently(peers: object) -> None:
    police, thief = peers
    for url in (police.url, thief.url):
        assert call(url, "negotiate", "config_proposal", encode_proposal(proposal())) is None
