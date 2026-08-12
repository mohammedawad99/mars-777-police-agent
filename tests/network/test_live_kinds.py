"""Every peer kind that can be reached without a second group, over the public route.

A public tool-surface discovery is **not** a public kind proof: `list_tools`
returning four names says nothing about whether a `config_lock` payload ever
crossed the tunnel. Each kind below is sent through the real ngrok HTTPS URL and
confirmed against what the remote **application** recorded receiving.

All of it runs inside **one held `PeerClient` session**. That is the production
lifecycle this stage introduced, and it is also what makes the suite reliable:
one session per operation measured 20/30 over a real tunnel, one session for all
of them measured 30/30, in both experiment orders.
"""

import asyncio

from conftest import LivePeer
from live_support import TIMEOUT, requires_live_ngrok
from peer_ops import (
    ILLEGAL_HINT,
    acknowledgement,
    audit_document,
    commitment,
    final_nonce,
    lock_evidence,
    proposal,
    reveal,
    step0_exchange,
)

from mars777_police.transport.client import PeerClient
from mars777_police.transport.codec_declaration import encode_step0
from mars777_police.transport.codec_final import encode_final_nonce
from mars777_police.transport.codec_pregame import encode_lock, encode_proposal
from mars777_police.transport.codec_turn import (
    encode_acknowledgement,
    encode_commitment,
    encode_reveal,
)

pytestmark = requires_live_ngrok


def test_every_peer_kind_crosses_the_public_route(public_peer: LivePeer) -> None:
    """All nine kinds, one held session, each confirmed by the remote application."""
    _, endpoint, peer = public_peer

    async def drive() -> tuple[bool, bool]:
        async with PeerClient(endpoint.url, timeout=TIMEOUT) as client:
            await client.complete("negotiate", "step0", encode_step0(step0_exchange()))
            await client.complete("negotiate", "config_proposal", encode_proposal(proposal()))
            await client.complete("negotiate", "config_lock", encode_lock(lock_evidence()))
            await client.complete("receive_turn", "commitment", encode_commitment(commitment()))
            await client.complete(
                "receive_turn", "acknowledgement", encode_acknowledgement(acknowledgement())
            )
            legal = await client.outcome(encode_reveal(reveal()))
            illegal = await client.outcome(encode_reveal(reveal(ILLEGAL_HINT)))
            await client.complete(
                "submit_audit", "final_nonce_reveal", encode_final_nonce(final_nonce())
            )
            await client.complete("submit_audit", "audit_disclosure", audit_document())
            return legal, illegal

    legal, illegal = asyncio.run(drive())

    assert legal is True, "a legal action must be accepted across the public route"
    assert illegal is False, "False is the game-legality verdict and nothing else"

    seen = peer.received()
    for kind in (
        "step0",
        "config_proposal",
        "config_lock",
        "commitment",
        "acknowledgement",
        "reveal",
        "final_nonce_reveal",
        "audit_disclosure",
    ):
        assert kind in seen, f"{kind} never reached the remote application"


def test_all_four_tool_surfaces_were_actually_invoked(public_peer: LivePeer) -> None:
    """Not discovery - invocation. Every tool carried at least one real payload."""
    _, _endpoint, peer = public_peer
    seen = set(peer.received())
    assert {"step0", "config_proposal", "config_lock"} <= seen
    assert {"commitment", "acknowledgement", "reveal"} <= seen
    assert {"final_nonce_reveal", "audit_disclosure"} <= seen
