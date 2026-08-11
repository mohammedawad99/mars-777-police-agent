"""All nine kinds through the real server, into the real application owners.

This is the proof Stage 5-R3 could not deliver: a production FastMCP server with
a production `PeerOperations` behind it, and no test double supplying any
application behaviour. One persistent session carries the whole sequence, so the
identity that Step-0 established is the one every later call is judged against.
"""

import asyncio
from collections.abc import Iterator

import pytest
import session_calls
from session_process import SessionPeer

from mars777_police.transport.client import PeerClient
from mars777_police.transport.server import PEER_TOOLS

TIMEOUT = 20.0


@pytest.fixture(scope="module")
def peer() -> Iterator[SessionPeer]:
    """One production peer process for this module."""
    with SessionPeer() as running:
        yield running


async def drive(url: str) -> list[object]:
    """Send every kind on one held session and collect each raw result."""
    results: list[object] = []
    async with PeerClient(url, timeout=TIMEOUT) as client:
        for tool, kind, payload in session_calls.payloads():
            results.append(await client.call(tool, kind, payload))
    return results


def test_every_kind_reaches_a_real_owner_on_one_session(peer: SessionPeer) -> None:
    """Nine kinds, nine owners, one authenticated session, zero doubles."""
    results = asyncio.run(drive(peer.url))
    assert len(results) == 9
    assert results[5] is True
    assert isinstance(results[8], str) and len(results[8]) == 64
    assert [r for i, r in enumerate(results) if i not in {5, 8}] == [None] * 7


def test_the_kind_vocabulary_sent_is_exactly_the_frozen_nine(peer: SessionPeer) -> None:
    assert session_calls.KINDS == [
        "step0",
        "config_proposal",
        "config_lock",
        "commitment",
        "acknowledgement",
        "reveal",
        "final_nonce_reveal",
        "audit_disclosure",
        "result_agreement",
    ]


def test_the_production_server_still_publishes_exactly_four_tools(peer: SessionPeer) -> None:
    from fastmcp import Client
    from fastmcp.client.transports import StreamableHttpTransport

    async def names() -> list[str]:
        async with Client(StreamableHttpTransport(peer.url), timeout=TIMEOUT) as client:
            return sorted(tool.name for tool in await client.list_tools())

    assert asyncio.run(names()) == sorted(PEER_TOOLS)


def test_no_tool_schema_asks_the_client_for_an_identity(peer: SessionPeer) -> None:
    """The session context is server-derived; it never appears on the wire."""
    from fastmcp import Client
    from fastmcp.client.transports import StreamableHttpTransport

    async def schemas() -> dict[str, list[str]]:
        async with Client(StreamableHttpTransport(peer.url), timeout=TIMEOUT) as client:
            return {t.name: sorted(t.inputSchema["properties"]) for t in await client.list_tools()}

    published = asyncio.run(schemas())
    assert set(published) == set(PEER_TOOLS)
    for properties in published.values():
        assert properties == ["request"]
    text = str(published)
    for forbidden in ("session", "sender_id", "context", "auth_tag", "token"):
        assert forbidden not in text
