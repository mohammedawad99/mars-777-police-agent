"""The `PRD05-FR-021` readiness gate: exactly ten checks, in requirement order.

The gate **consumes** facts; it does not re-derive them. Step-0 authentication,
config equality, peer identity and the series convention each already have an
authoritative owner elsewhere in the application, and a gate that re-implemented
any of them would create a second answer that could disagree with the first.
`ReadinessFacts` is therefore a plain record of what those owners concluded.

Three of the ten carry a PRD-named local reason - (c) `E-NET-NOT-PUBLIC`, (d)
`E-NET-STALE-ENDPOINT` when a bound ingress went stale, and (j)
`E-NET-CONVENTION-UNSET`. The rest fail without one, because inventing reason
strings for them would grow the vocabulary the PRD deliberately fixed.

`FR-020` is the point of the whole thing: a healthy local process is explicitly
**not** sufficient evidence, so (a) passing on its own means nothing.
"""

from dataclasses import dataclass

from .public_endpoint_values import OpponentPublicPeerEndpoint, OwnPublicPeerEndpoint
from .public_readiness_values import (
    CheckOutcome,
    PublicReadinessReason,
    PublicReadinessVerdict,
    ReadinessCheck,
)


@dataclass(frozen=True, slots=True)
class ReadinessFacts:
    """Everything the ten checks need, each supplied by its authoritative owner."""

    local_server_bound: bool
    tunnel_established: bool
    own_public_endpoint: OwnPublicPeerEndpoint | None
    own_endpoint_is_public: bool
    own_endpoint_stale: bool
    opponent_endpoint: OpponentPublicPeerEndpoint | None
    outbound_proven: bool
    inbound_proven: bool
    peer_identity_matches: bool
    step0_authenticated: bool
    config_unmutated_since_lock: bool
    convention_frozen: bool


def _outcome(
    check: ReadinessCheck, passed: bool, reason: PublicReadinessReason | None = None
) -> CheckOutcome:
    return CheckOutcome(check, passed, None if passed else reason)


def evaluate(facts: ReadinessFacts) -> PublicReadinessVerdict:
    """Evaluate (a)-(j) and return the machine-readable verdict."""
    public_ok = (
        facts.own_public_endpoint is not None
        and facts.own_endpoint_is_public
        and not facts.own_endpoint_stale
    )
    public_reason = (
        PublicReadinessReason.STALE_ENDPOINT
        if facts.own_endpoint_stale
        else PublicReadinessReason.NOT_PUBLIC
    )
    return PublicReadinessVerdict(
        (
            _outcome(ReadinessCheck.LOCAL_SERVER_BOUND, facts.local_server_bound),
            _outcome(ReadinessCheck.PUBLIC_TUNNEL_ESTABLISHED, facts.tunnel_established),
            _outcome(ReadinessCheck.OWN_PUBLIC_URL_NON_LOOPBACK, public_ok, public_reason),
            _outcome(ReadinessCheck.OPPONENT_ENDPOINT_KNOWN, facts.opponent_endpoint is not None),
            _outcome(ReadinessCheck.OUTBOUND_REACHABILITY, facts.outbound_proven),
            _outcome(ReadinessCheck.INBOUND_REACHABILITY, facts.inbound_proven),
            _outcome(ReadinessCheck.EXPECTED_PEER_IDENTITY, facts.peer_identity_matches),
            _outcome(ReadinessCheck.STEP0_AUTHENTICATED, facts.step0_authenticated),
            _outcome(ReadinessCheck.CONFIG_UNMUTATED_SINCE_LOCK, facts.config_unmutated_since_lock),
            _outcome(
                ReadinessCheck.PROFILE_AND_CONVENTION_FROZEN,
                facts.convention_frozen,
                PublicReadinessReason.CONVENTION_UNSET,
            ),
        )
    )
