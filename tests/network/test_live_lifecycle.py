"""Readiness, outage and role-switch behaviour over the live public route.

The readiness verdict here is expected to remain `NOT_READY`. That is the point:
our own ingress is healthy and counted play is still refused, because the
opponent-derived facts genuinely do not exist yet. Fabricating them to force a
green verdict is exactly what this stage must not do.
"""

import asyncio

import pytest
from conftest import LivePeer
from live_support import UNREACHABLE, service
from net_builders import declaration_at
from peer_ops import reveal
from peer_process import free_port

from mars777_police.app.peer_supervision import PeerDeadline, TimeoutPolicy
from mars777_police.app.protocol_errors import (
    AuthFailureError,
    MalformedMessageError,
    ReportDisagreeError,
)
from mars777_police.app.public_endpoint_values import LocalPeerEndpoint
from mars777_police.app.public_network_workflow import CountedPlayNotReadyError
from mars777_police.transport.client import PeerClient
from mars777_police.transport.codec_turn import encode_reveal

pytestmark = requires_live_ngrok = __import__("live_support").requires_live_ngrok


def test_the_readiness_gate_refuses_counted_play_without_opponent_facts(
    public_peer: LivePeer,
) -> None:
    """Our ingress is healthy and counted play is still refused. Fail-closed."""
    route, endpoint, peer = public_peer
    svc = service(route)
    svc.local = LocalPeerEndpoint("127.0.0.1", peer.port)
    svc.own = endpoint
    svc.declare(declaration_at)
    facts = svc.facts(
        opponent=None,
        outbound_proven=False,
        inbound_proven=False,
        peer_identity_matches=False,
        step0_authenticated=True,
        config_unmutated_since_lock=True,
        convention_frozen=False,
    )
    verdict = svc.readiness(facts)
    assert not verdict.is_ready
    assert {outcome.check.value for outcome in verdict.failures} == {"d", "e", "f", "g", "j"}
    with pytest.raises(CountedPlayNotReadyError):
        svc.require_counted_play(facts)


def test_the_declaration_binds_the_live_public_endpoint(public_peer: LivePeer) -> None:
    """`mcp_endpoint` is the discovered public URL, authenticated afterwards."""
    route, endpoint, peer = public_peer
    svc = service(route)
    svc.local = LocalPeerEndpoint("127.0.0.1", peer.port)
    svc.own = endpoint
    exchange = svc.declare(declaration_at)
    team = exchange.declaration.teams.group_a
    assert team is not None
    assert team.mcp_endpoint == endpoint.url
    assert team.mcp_endpoint.startswith("https://")
    assert svc.binding.authenticated == endpoint


def test_an_unreachable_public_route_is_a_transport_failure_not_a_legality_false(
    public_peer: LivePeer,
) -> None:
    """A dead route makes the peer unreachable - never illegal, never unauthentic."""
    _, endpoint, _peer = public_peer
    assert endpoint.url != UNREACHABLE
    with pytest.raises(Exception) as raised:
        asyncio.run(
            PeerClient(UNREACHABLE, PeerDeadline(TimeoutPolicy(10.0))).outcome(
                encode_reveal(reveal())
            )
        )
    assert not isinstance(
        raised.value, AuthFailureError | MalformedMessageError | ReportDisagreeError
    )
    assert raised.value is not False


def test_the_ingress_survives_a_role_switch_behind_it(public_peer: LivePeer) -> None:
    """`FR-015a`/`FR-043`: the local upstream may move; the declared ingress may not.

    The restart-stability and role-switch probes were run against the live agent
    before this stage wrote any code, and both preserved the hostname. Here the
    production binding is asserted to treat that correctly - an unchanged public
    identity permits local recovery, and a changed one would refuse it.
    """
    route, endpoint, _ = public_peer
    svc = service(route)
    svc.binding.bind(endpoint)
    assert svc.binding.observe(endpoint)
    moved = LocalPeerEndpoint("127.0.0.1", free_port())
    assert svc.recover_behind_ingress(moved) == moved
    assert not svc.binding.stale
    assert svc.binding.reason is None
