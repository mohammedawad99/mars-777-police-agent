"""Peer error identities survive the tunnel unchanged.

Every refusal below is produced by a **production runtime** on the far side -
`Step0Runtime.accept` and `ConfigNegotiationRuntime.accept` - and not by a
handler that raises on command. That distinction is the whole point: an injected
exception would prove the error mapping, not that a real application rejection
keeps its identity across a public proxy.

All five run inside **one held session**, which also proves a refusal does not
poison the session for the operations that follow it.
"""

import asyncio
from dataclasses import replace

import pytest
from conftest import LivePeer
from live_support import TIMEOUT, requires_live_ngrok
from peer_ops import proposal, step0_exchange
from r16_builders import PROFILES

from mars777_police.app.interop_profiles import SeriesConvention
from mars777_police.app.peer_supervision import PeerDeadline, TimeoutPolicy
from mars777_police.app.protocol_errors import (
    AuthFailureError,
    ConventionMismatchError,
    MalformedMessageError,
    StaleMessageError,
)
from mars777_police.transport.client import PeerClient
from mars777_police.transport.codec_declaration import encode_step0
from mars777_police.transport.codec_pregame import encode_proposal

pytestmark = requires_live_ngrok


def other_convention() -> SeriesConvention:
    return (
        SeriesConvention.FIXED_ROLE
        if PROFILES.series_convention is not SeriesConvention.FIXED_ROLE
        else SeriesConvention.REFERENCE_ODD_EVEN_ALTERNATION
    )


def test_every_feasible_peer_identity_survives_the_public_tunnel(
    public_peer: LivePeer,
) -> None:
    """Four identities, each raised by a real runtime, all in one held session."""
    _, endpoint, _peer = public_peer
    exchange = step0_exchange()
    stale = replace(
        exchange,
        declaration=replace(exchange.declaration, game_id="mars777-vs-someone-else-2026w1-uid9999"),
    )
    forged = replace(exchange, auth=replace(exchange.auth, value="0" * 64))
    divergent = replace(
        proposal(), profiles=replace(PROFILES, series_convention=other_convention())
    )
    seen: dict[str, str] = {}

    async def drive() -> None:
        async with PeerClient(endpoint.url, PeerDeadline(TimeoutPolicy(TIMEOUT))) as client:
            for label, call in (
                ("malformed-kind", client.complete("negotiate", "commitment", {"nonsense": True})),
                ("malformed-payload", client.complete("negotiate", "step0", {"declaration": 7})),
                ("stale", client.complete("negotiate", "step0", encode_step0(stale))),
                ("auth", client.complete("negotiate", "step0", encode_step0(forged))),
                (
                    "convention",
                    client.complete("negotiate", "config_proposal", encode_proposal(divergent)),
                ),
            ):
                try:
                    await call
                except Exception as failure:
                    seen[label] = getattr(failure, "error_id", type(failure).__name__)

    asyncio.run(drive())

    assert seen["malformed-kind"] == MalformedMessageError.error_id
    assert seen["malformed-payload"] == MalformedMessageError.error_id
    assert seen["stale"] == StaleMessageError.error_id
    assert seen["auth"] == AuthFailureError.error_id
    assert seen["convention"] == ConventionMismatchError.error_id


def test_no_public_failure_was_reduced_to_a_boolean(public_peer: LivePeer) -> None:
    """`False` never stands in for a protocol failure, only for game legality."""
    _, endpoint, _peer = public_peer

    async def drive() -> None:
        async with PeerClient(endpoint.url, PeerDeadline(TimeoutPolicy(TIMEOUT))) as client:
            await client.outcome({"kind": "reveal", "payload": {"bad": 1}})

    with pytest.raises(MalformedMessageError):
        asyncio.run(drive())
