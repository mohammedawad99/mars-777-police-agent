"""What happens when the public endpoint changes after it has been authenticated.

`PRD05-FR-015b` is unusually strict, and deliberately: once a declaration
carrying `mcp_endpoint` has been authenticated, a *different* public URL may not
silently mutate it, may not be re-advertised as though nothing happened, and may
not simply continue. Counted play pauses; the same ingress is preferred; a
genuinely different ingress needs a new declaration boundary.

`FR-015a` is the other half and is what makes the group-level model work: local
changes *behind* the same public ingress - a new bind port, a restarted process,
a switch from the Police role process to the Thief one - are permitted and
**do not** change the declared endpoint. Measured against the real agent, a
restart and a role switch both preserved the ingress, so this is the common path
rather than a theoretical one.

This type holds exactly that distinction and nothing else. It computes no
digest, sends no message and decides no sanction.
"""

from dataclasses import dataclass, field

from .public_endpoint_values import LocalPeerEndpoint, OwnPublicPeerEndpoint
from .public_readiness_values import PublicReadinessReason


@dataclass(slots=True)
class EndpointBinding:
    """The authenticated public endpoint, and how observations compare to it."""

    authenticated: OwnPublicPeerEndpoint | None = field(default=None)
    stale: bool = field(default=False)

    def bind(self, endpoint: OwnPublicPeerEndpoint) -> None:
        """Record the endpoint an authenticated declaration committed to.

        Binding twice to a different value is refused rather than overwritten -
        silently rebinding is precisely the mutation FR-015b prohibits.
        """
        if self.authenticated is not None and self.authenticated != endpoint:
            raise ValueError("an authenticated endpoint may not be rebound in place")
        self.authenticated = endpoint

    def observe(self, endpoint: OwnPublicPeerEndpoint) -> bool:
        """Compare a freshly discovered endpoint with the authenticated one.

        Returns whether the ingress identity survived. An unbound binding
        accepts anything - nothing has been promised to a peer yet.
        """
        if self.authenticated is None:
            return True
        if self.authenticated == endpoint:
            self.stale = False
            return True
        self.stale = True
        return False

    def recover_local(self, local: LocalPeerEndpoint) -> LocalPeerEndpoint:
        """Accept a new local upstream behind an unchanged public ingress (FR-015a).

        The declaration is untouched: what changed is which local process the
        group-level ingress fronts, which no peer can observe and FR-043 permits.
        """
        if self.stale:
            raise ValueError("the public ingress is stale; local recovery cannot apply")
        return local

    @property
    def reason(self) -> PublicReadinessReason | None:
        """The local refusal reason implied by the current binding state."""
        return PublicReadinessReason.STALE_ENDPOINT if self.stale else None
