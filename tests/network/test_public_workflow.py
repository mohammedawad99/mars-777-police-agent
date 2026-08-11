"""The production owner: it establishes, declares, and refuses counted play.

This is the file that answers the R17 lesson. The readiness gate is not reachable
only from a test - `PublicNetworkService.require_counted_play` calls it, and a
caller that ignores the verdict cannot proceed because the refusal is raised.
"""

import pytest
from net_builders import declaration_at, runtime
from net_fakes import OTHER_URL, PUBLIC_URL, FakeIngress, FakeResolver
from r16_builders import GROUP_A

from mars777_police.app.public_endpoint_values import (
    LocalPeerEndpoint,
    OpponentPublicPeerEndpoint,
    OwnPublicPeerEndpoint,
)
from mars777_police.app.public_ingress import PublicIngressError
from mars777_police.app.public_network_workflow import (
    CountedPlayNotReadyError,
    PublicNetworkService,
)
from mars777_police.protocol.canonical import canonical_json_bytes
from mars777_police.protocol.declaration import step0_core

LOCAL = LocalPeerEndpoint("127.0.0.1", 8801)
OPPONENT = OpponentPublicPeerEndpoint("https://opponent.example/mcp")


def service(ingress: FakeIngress | None = None) -> PublicNetworkService:
    return PublicNetworkService(ingress or FakeIngress(), FakeResolver(), runtime())


def ready_facts(svc: PublicNetworkService) -> object:
    return svc.facts(
        opponent=OPPONENT,
        outbound_proven=True,
        inbound_proven=True,
        peer_identity_matches=True,
        step0_authenticated=True,
        config_unmutated_since_lock=True,
        convention_frozen=True,
    )


def test_establishing_adopts_the_discovered_public_endpoint() -> None:
    svc = service()
    assert svc.establish(LOCAL).url == PUBLIC_URL
    assert svc.local == LOCAL and svc.own is not None


def test_a_private_discovered_endpoint_is_refused_and_the_route_closed() -> None:
    ingress = FakeIngress(endpoint=OwnPublicPeerEndpoint("https://localhost/mcp"))
    svc = service(ingress)
    with pytest.raises(PublicIngressError, match="counted play"):
        svc.establish(LOCAL)
    assert ingress.closed == 1


def test_declaring_before_establishing_is_refused() -> None:
    with pytest.raises(PublicIngressError, match="no public endpoint"):
        service().declare(declaration_at)


def test_the_declaration_carries_the_public_endpoint_and_is_authenticated_after() -> None:
    """The frozen order: discover, declare, then authenticate."""
    svc = service()
    endpoint = svc.establish(LOCAL)
    exchange = svc.declare(declaration_at)
    team = exchange.declaration.teams.group_a
    assert team is not None
    assert team.mcp_endpoint == endpoint.url
    assert team.mcp_endpoint != LOCAL.url
    assert svc.binding.authenticated == endpoint


def test_the_authenticated_bytes_bind_that_exact_endpoint() -> None:
    """Changing the endpoint changes the authenticated core, so it cannot be swapped."""
    svc = service()
    endpoint = svc.establish(LOCAL)
    exchange = svc.declare(declaration_at)
    core = canonical_json_bytes(step0_core(exchange.declaration, GROUP_A))
    assert endpoint.url.encode() in core
    other = canonical_json_bytes(
        step0_core(declaration_at(OwnPublicPeerEndpoint(OTHER_URL)), GROUP_A)
    )
    assert core != other
    assert runtime().auth.verify(exchange.declaration, GROUP_A, exchange.auth)


def test_a_swapped_endpoint_no_longer_verifies_against_the_original_proof() -> None:
    svc = service()
    svc.establish(LOCAL)
    exchange = svc.declare(declaration_at)
    swapped = declaration_at(OwnPublicPeerEndpoint(OTHER_URL))
    assert not runtime().auth.verify(swapped, GROUP_A, exchange.auth)


def test_counted_play_is_refused_while_opponent_facts_are_missing() -> None:
    """The live R18-R1 condition: our ingress is healthy, readiness still refuses."""
    svc = service()
    svc.establish(LOCAL)
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
    assert {o.check.value for o in verdict.failures} == {"d", "e", "f", "g", "j"}
    with pytest.raises(CountedPlayNotReadyError, match="refused counted play"):
        svc.require_counted_play(facts)


def test_counted_play_is_granted_when_every_authoritative_fact_holds() -> None:
    svc = service()
    svc.establish(LOCAL)
    svc.declare(declaration_at)
    assert svc.require_counted_play(ready_facts(svc)).is_ready  # type: ignore[arg-type]


def test_the_refusal_is_local_and_assigns_no_sanction() -> None:
    from mars777_police.app.protocol_errors import PeerProtocolError

    assert not issubclass(CountedPlayNotReadyError, PeerProtocolError)
    assert "TECHNICAL" not in str(CountedPlayNotReadyError.__doc__)
