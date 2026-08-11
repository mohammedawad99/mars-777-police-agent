"""The provider-neutral public-ingress port.

`PRD05-FR-005` requires the tunnel provider to sit behind a port, with no
provider name, SDK or provider-specific URL scheme reachable from application or
domain logic. This is that port. Nothing here mentions a provider, a process, an
HTTP client or a config file, and nothing here is FastMCP-aware.

**It is not `PeerTransportPort`.** That port carries peer *messages* outbound.
This one manages the *route* by which a peer reaches us inbound. Merging them
would put process management behind a method that otherwise sends a commitment,
and a tunnel restart would become indistinguishable from a protocol call.

Like the Stage-4E-R16 runtime ports, this is an implementation seam rather than
a new entry in the frozen architecture-port register: the register already
describes a stable group-level ingress (`API_BOUNDARIES.md` O4), and this is how
that description becomes executable.
"""

from typing import Protocol

from .public_endpoint_values import LocalPeerEndpoint, OwnPublicPeerEndpoint


class PublicIngressPort(Protocol):
    """One group-level public route to one local FastMCP upstream."""

    def open(self, local: LocalPeerEndpoint) -> OwnPublicPeerEndpoint:
        """Expose *local* publicly and return the resulting public MCP endpoint.

        Raises the project's local ingress failure when the route cannot be
        established; it never raises a peer protocol error, because no peer is
        involved in our own tunnel coming up.
        """
        ...

    def current(self) -> OwnPublicPeerEndpoint | None:
        """The public endpoint currently served, or `None` when closed."""
        ...

    def is_live(self) -> bool:
        """Whether the route is presently established."""
        ...

    def close(self) -> None:
        """Tear the route down. Safe to call when already closed."""
        ...


class PublicIngressError(Exception):
    """A local failure to establish, discover or maintain our public route.

    Deliberately **not** a `PeerProtocolError`: FR-015c classifies endpoint
    unavailability as a transport failure, not an integrity failure, and no
    sanction follows from it.
    """
