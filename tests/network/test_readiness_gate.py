"""`PRD05-FR-021` (a)-(j): exactly ten checks, and no shortcut to ready.

`FR-020` is what most of these assert indirectly - a healthy local process is
explicitly not sufficient evidence, so nine passing checks are still not ready.
"""

import pytest
from net_fakes import PUBLIC_URL

from mars777_police.app.public_endpoint_values import (
    OpponentPublicPeerEndpoint,
    OwnPublicPeerEndpoint,
)
from mars777_police.app.public_readiness_gate import ReadinessFacts, evaluate
from mars777_police.app.public_readiness_values import (
    CHECK_ORDER,
    PublicReadinessReason,
    ReadinessCheck,
)

OWN = OwnPublicPeerEndpoint(PUBLIC_URL)
OPPONENT = OpponentPublicPeerEndpoint("https://opponent.example/mcp")


def facts(**overrides: object) -> ReadinessFacts:
    base: dict[str, object] = {
        "local_server_bound": True,
        "tunnel_established": True,
        "own_public_endpoint": OWN,
        "own_endpoint_is_public": True,
        "own_endpoint_stale": False,
        "opponent_endpoint": OPPONENT,
        "outbound_proven": True,
        "inbound_proven": True,
        "peer_identity_matches": True,
        "step0_authenticated": True,
        "config_unmutated_since_lock": True,
        "convention_frozen": True,
    }
    base.update(overrides)
    return ReadinessFacts(**base)  # type: ignore[arg-type]


def test_all_ten_authoritative_facts_produce_ready() -> None:
    """The synthetic proof that the gate CAN pass - never claimed of the live run."""
    verdict = evaluate(facts())
    assert verdict.is_ready
    assert verdict.failures == ()
    assert tuple(o.check for o in verdict.outcomes) == CHECK_ORDER


@pytest.mark.parametrize(
    ("override", "check"),
    [
        ({"local_server_bound": False}, ReadinessCheck.LOCAL_SERVER_BOUND),
        ({"tunnel_established": False}, ReadinessCheck.PUBLIC_TUNNEL_ESTABLISHED),
        ({"own_public_endpoint": None}, ReadinessCheck.OWN_PUBLIC_URL_NON_LOOPBACK),
        ({"own_endpoint_is_public": False}, ReadinessCheck.OWN_PUBLIC_URL_NON_LOOPBACK),
        ({"opponent_endpoint": None}, ReadinessCheck.OPPONENT_ENDPOINT_KNOWN),
        ({"outbound_proven": False}, ReadinessCheck.OUTBOUND_REACHABILITY),
        ({"inbound_proven": False}, ReadinessCheck.INBOUND_REACHABILITY),
        ({"peer_identity_matches": False}, ReadinessCheck.EXPECTED_PEER_IDENTITY),
        ({"step0_authenticated": False}, ReadinessCheck.STEP0_AUTHENTICATED),
        ({"config_unmutated_since_lock": False}, ReadinessCheck.CONFIG_UNMUTATED_SINCE_LOCK),
        ({"convention_frozen": False}, ReadinessCheck.PROFILE_AND_CONVENTION_FROZEN),
    ],
)
def test_any_single_missing_fact_refuses_readiness(
    override: dict[str, object], check: ReadinessCheck
) -> None:
    verdict = evaluate(facts(**override))
    assert not verdict.is_ready
    assert [o.check for o in verdict.failures] == [check]


def test_a_non_public_endpoint_carries_the_prd_named_reason() -> None:
    verdict = evaluate(facts(own_endpoint_is_public=False))
    assert PublicReadinessReason.NOT_PUBLIC in verdict.reasons


def test_a_stale_endpoint_is_reported_as_stale_not_as_not_public() -> None:
    verdict = evaluate(facts(own_endpoint_stale=True))
    assert verdict.reasons == (PublicReadinessReason.STALE_ENDPOINT,)


def test_an_unset_convention_carries_its_own_prd_reason() -> None:
    verdict = evaluate(facts(convention_frozen=False))
    assert verdict.reasons == (PublicReadinessReason.CONVENTION_UNSET,)


def test_a_healthy_local_process_alone_is_not_readiness() -> None:
    """`FR-020` stated as a test: only (a) true is still refused."""
    only_local = evaluate(
        facts(
            tunnel_established=False,
            own_public_endpoint=None,
            own_endpoint_is_public=False,
            opponent_endpoint=None,
            outbound_proven=False,
            inbound_proven=False,
            peer_identity_matches=False,
            step0_authenticated=False,
            config_unmutated_since_lock=False,
            convention_frozen=False,
        )
    )
    assert not only_local.is_ready
    assert len(only_local.failures) == 9


def test_the_gate_has_no_eleventh_check() -> None:
    assert len(evaluate(facts()).outcomes) == 10
