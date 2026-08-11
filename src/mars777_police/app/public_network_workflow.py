"""The production owner of our group's public ingress, end to end.

R17 taught the lesson this module exists to avoid: a guard nothing calls is not
a guard. The readiness gate, the endpoint binding and the publicity policy are
all reachable from here, and this service is what an orchestrator asks before
counted play - so `NOT_READY` refuses progression in the runtime rather than
only in a test.

**The order is the requirement.** `mcp_endpoint` lives inside the Step-0
authenticated core, so the public endpoint must be known *before* the
declaration is built and authenticated. Building a declaration with a local
address and swapping in the public URL afterwards would leave authenticated
bytes that no longer describe what they claim to - which is exactly what
`FR-015b` forbids and what `bind` here makes impossible.

The service owns checks (a), (b) and (c) because they are facts about our own
ingress. The other seven arrive from the runtimes that already own them; this
module never re-derives an authentication, a config digest or a convention.
"""

from collections.abc import Callable
from dataclasses import dataclass, field

from .declaration_values import Declaration
from .peer_pregame_messages import Step0DeclarationExchange
from .public_endpoint_binding import EndpointBinding
from .public_endpoint_policy import HostResolver, is_public_endpoint
from .public_endpoint_values import (
    LocalPeerEndpoint,
    OpponentPublicPeerEndpoint,
    OwnPublicPeerEndpoint,
)
from .public_ingress import PublicIngressError, PublicIngressPort
from .public_readiness_gate import ReadinessFacts, evaluate
from .public_readiness_values import PublicReadinessVerdict
from .step0_runtime import Step0Runtime


class CountedPlayNotReadyError(Exception):
    """Counted play was attempted while the readiness gate refused it.

    Local and deliberately **not** a `PeerProtocolError`: refusing to start is
    not a peer failure, and `FR-015c` forbids inventing a sanction for it.
    """


@dataclass(slots=True)
class PublicNetworkService:
    """Our group's single public ingress, from exposure to counted-play consent."""

    ingress: PublicIngressPort
    resolver: HostResolver
    step0: Step0Runtime
    binding: EndpointBinding = field(default_factory=EndpointBinding)
    local: LocalPeerEndpoint | None = field(default=None)
    own: OwnPublicPeerEndpoint | None = field(default=None)

    def establish(self, local: LocalPeerEndpoint) -> OwnPublicPeerEndpoint:
        """Open the route and adopt the discovered endpoint, refusing a private one."""
        endpoint = self.ingress.open(local)
        if not is_public_endpoint(endpoint, self.resolver):
            self.ingress.close()
            raise PublicIngressError("the discovered endpoint is not usable for counted play")
        self.local, self.own = local, endpoint
        return endpoint

    def declare(
        self, build: Callable[[OwnPublicPeerEndpoint], Declaration]
    ) -> Step0DeclarationExchange:
        """Build the declaration **from** the public endpoint, then authenticate it."""
        if self.own is None:
            raise PublicIngressError("no public endpoint has been established yet")
        exchange = self.step0.outbound(build(self.own))
        self.binding.bind(self.own)
        return exchange

    def rediscover(self) -> bool:
        """Re-read the live endpoint and report whether the ingress identity held.

        A closed route is not a changed one: it leaves the binding alone so a
        transient outage cannot be mistaken for `FR-015b` replacement.
        """
        endpoint = self.ingress.current()
        if endpoint is None:
            return False
        self.own = endpoint
        return self.binding.observe(endpoint)

    def recover_behind_ingress(self, local: LocalPeerEndpoint) -> LocalPeerEndpoint:
        """Adopt a new local upstream behind an unchanged public ingress (`FR-015a`)."""
        self.local = self.binding.recover_local(local)
        return self.local

    def facts(
        self,
        *,
        opponent: OpponentPublicPeerEndpoint | None,
        outbound_proven: bool,
        inbound_proven: bool,
        peer_identity_matches: bool,
        step0_authenticated: bool,
        config_unmutated_since_lock: bool,
        convention_frozen: bool,
    ) -> ReadinessFacts:
        """Combine our own ingress facts with those their owners supply."""
        return ReadinessFacts(
            local_server_bound=self.local is not None,
            tunnel_established=self.ingress.is_live(),
            own_public_endpoint=self.own,
            own_endpoint_is_public=self.own is not None
            and is_public_endpoint(self.own, self.resolver),
            own_endpoint_stale=self.binding.stale,
            opponent_endpoint=opponent,
            outbound_proven=outbound_proven,
            inbound_proven=inbound_proven,
            peer_identity_matches=peer_identity_matches,
            step0_authenticated=step0_authenticated,
            config_unmutated_since_lock=config_unmutated_since_lock,
            convention_frozen=convention_frozen,
        )

    def readiness(self, facts: ReadinessFacts) -> PublicReadinessVerdict:
        """The `FR-021` verdict for the supplied facts."""
        return evaluate(facts)

    def require_counted_play(self, facts: ReadinessFacts) -> PublicReadinessVerdict:
        """Consent to counted play, or refuse with the failing checks (`FR-020`).

        This is the production refusal. A caller that ignores the verdict cannot
        proceed, because the refusal is raised rather than returned.
        """
        verdict = self.readiness(facts)
        if not verdict.is_ready:
            failing = ", ".join(outcome.check.value for outcome in verdict.failures)
            raise CountedPlayNotReadyError(f"public readiness refused counted play: {failing}")
        return verdict
