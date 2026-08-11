"""`FR-015a` recovery and `FR-015b` refusal, which are the same comparison.

The measured agent kept one hostname across a restart and across a role switch,
so same-ingress recovery is the ordinary path; the replacement path still has to
exist, because a stable domain is an account property and not a guarantee.
"""

import pytest
from net_builders import declaration_at, runtime
from net_fakes import OTHER_URL, PUBLIC_URL, FakeIngress, FakeResolver

from mars777_police.app.public_endpoint_binding import EndpointBinding
from mars777_police.app.public_endpoint_values import LocalPeerEndpoint, OwnPublicPeerEndpoint
from mars777_police.app.public_network_workflow import PublicNetworkService
from mars777_police.app.public_readiness_values import PublicReadinessReason

OWN = OwnPublicPeerEndpoint(PUBLIC_URL)
OTHER = OwnPublicPeerEndpoint(OTHER_URL)
LOCAL = LocalPeerEndpoint("127.0.0.1", 8801)


def test_an_unbound_binding_accepts_anything() -> None:
    binding = EndpointBinding()
    assert binding.observe(OTHER)
    assert binding.reason is None


def test_the_same_ingress_survives_and_stays_unstale() -> None:
    binding = EndpointBinding()
    binding.bind(OWN)
    assert binding.observe(OWN)
    assert not binding.stale and binding.reason is None


def test_a_different_ingress_marks_stale_without_mutating_the_binding() -> None:
    binding = EndpointBinding()
    binding.bind(OWN)
    assert not binding.observe(OTHER)
    assert binding.authenticated == OWN
    assert binding.stale
    assert binding.reason is PublicReadinessReason.STALE_ENDPOINT


def test_rebinding_to_a_different_endpoint_is_refused_outright() -> None:
    binding = EndpointBinding()
    binding.bind(OWN)
    binding.bind(OWN)
    with pytest.raises(ValueError, match="rebound"):
        binding.bind(OTHER)


def test_a_new_local_upstream_is_accepted_behind_an_unchanged_ingress() -> None:
    binding = EndpointBinding()
    binding.bind(OWN)
    binding.observe(OWN)
    moved = LocalPeerEndpoint("127.0.0.1", 8802)
    assert binding.recover_local(moved) == moved


def test_local_recovery_is_refused_once_the_ingress_is_stale() -> None:
    binding = EndpointBinding()
    binding.bind(OWN)
    binding.observe(OTHER)
    with pytest.raises(ValueError, match="stale"):
        binding.recover_local(LOCAL)


def test_the_workflow_rediscovers_the_same_ingress_after_a_role_switch() -> None:
    ingress = FakeIngress()
    svc = PublicNetworkService(ingress, FakeResolver(), runtime())
    svc.establish(LOCAL)
    svc.declare(declaration_at)
    assert svc.rediscover()
    moved = LocalPeerEndpoint("127.0.0.1", 8802)
    assert svc.recover_behind_ingress(moved) == moved
    assert not svc.binding.stale


def test_the_workflow_refuses_a_replaced_ingress_and_reports_it_stale() -> None:
    ingress = FakeIngress()
    svc = PublicNetworkService(ingress, FakeResolver(), runtime())
    svc.establish(LOCAL)
    svc.declare(declaration_at)
    ingress.endpoint = OTHER
    assert not svc.rediscover()
    assert svc.binding.stale
    facts = svc.facts(
        opponent=None,
        outbound_proven=True,
        inbound_proven=True,
        peer_identity_matches=True,
        step0_authenticated=True,
        config_unmutated_since_lock=True,
        convention_frozen=True,
    )
    assert PublicReadinessReason.STALE_ENDPOINT in svc.readiness(facts).reasons


def test_a_closed_route_is_an_outage_not_a_replacement() -> None:
    """An outage must not be mistaken for FR-015b: the binding is left alone."""
    ingress = FakeIngress()
    svc = PublicNetworkService(ingress, FakeResolver(), runtime())
    svc.establish(LOCAL)
    svc.declare(declaration_at)
    ingress.close()
    assert not svc.rediscover()
    assert not svc.binding.stale
