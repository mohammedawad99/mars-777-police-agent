"""Forty sequential peer operations over one public route, one held session.

This is the reliability gate the FIX2 measurement demanded. The same forty
operations opening a session each is precisely the pattern that failed from the
twenty-first onward over a real tunnel; through the production held lifecycle
they must all succeed, with no retry loop anywhere to manufacture the result.

`acknowledgement` is used throughout because it is inbound-only and carries no
game state: forty of them mutate nothing the rest of the suite depends on.
"""

import asyncio

from conftest import LivePeer
from live_support import TIMEOUT, requires_live_ngrok
from peer_ops import acknowledgement

from mars777_police.transport.client import PeerClient
from mars777_police.transport.codec_turn import encode_acknowledgement

pytestmark = requires_live_ngrok
OPERATIONS = 40


def test_forty_public_operations_succeed_inside_one_production_session(
    public_peer: LivePeer,
) -> None:
    """No reopened session, no retry, no pacing - just the production lifecycle."""
    _, endpoint, peer = public_peer
    before = peer.received().count("acknowledgement")

    async def drive() -> object:
        async with PeerClient(endpoint.url, timeout=TIMEOUT) as client:
            held = client._session
            for _ in range(OPERATIONS):
                await client.complete(
                    "receive_turn", "acknowledgement", encode_acknowledgement(acknowledgement())
                )
                assert client._session is held, "the session must not be reopened mid-run"
            return held

    held = asyncio.run(drive())

    assert held is not None
    after = peer.received().count("acknowledgement")
    assert after - before == OPERATIONS, "every operation must have reached the application"
