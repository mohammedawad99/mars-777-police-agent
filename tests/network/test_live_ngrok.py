"""Our group's public ingress itself: the endpoint value and the tool surface.

The peer **kinds** are proven in `test_live_kinds`, the identities in
`test_live_errors` and the result direction in `test_live_result`. This module
keeps only what is about the ingress rather than the protocol, which also keeps
the suite's MCP session count low - the free account meters consumption, and a
run that exhausts it proves nothing.
"""

import asyncio

from conftest import LivePeer
from live_support import TIMEOUT, requires_live_ngrok

from mars777_police.app.public_endpoint_policy import SystemHostResolver, is_public_endpoint
from mars777_police.transport.server import PEER_TOOLS

pytestmark = requires_live_ngrok


def test_the_public_endpoint_is_discovered_structurally_and_is_public(
    public_peer: LivePeer,
) -> None:
    route, endpoint, _peer = public_peer
    assert endpoint.url.startswith("https://")
    assert endpoint.url.endswith("/mcp")
    assert "//mcp" not in endpoint.url
    assert "127.0.0.1" not in endpoint.url and "localhost" not in endpoint.url
    assert "?" not in endpoint.url and "#" not in endpoint.url and "@" not in endpoint.url
    assert is_public_endpoint(endpoint, SystemHostResolver())
    assert route.is_live()


def test_the_four_tools_are_discovered_through_the_public_url(public_peer: LivePeer) -> None:
    """`list_tools` across the tunnel - a local call is explicitly not proof."""
    from fastmcp import Client
    from fastmcp.client.transports import StreamableHttpTransport

    _, endpoint, _peer = public_peer

    async def run() -> list[str]:
        async with Client(StreamableHttpTransport(endpoint.url), timeout=TIMEOUT) as client:
            return sorted(tool.name for tool in await client.list_tools())

    assert asyncio.run(run()) == sorted(PEER_TOOLS)
