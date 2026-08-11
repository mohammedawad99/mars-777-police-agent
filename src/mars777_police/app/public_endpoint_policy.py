"""Whether a discovered URL may be advertised for counted play.

`PRD05-FR-004` rejects an endpoint whose host resolves to loopback, link-local
or a private-only address, with reason `E-NET-NOT-PUBLIC`; `FR-014` forbids any
secret in the URL. Both are enforced here, and nowhere else, so there is one
answer to "is this endpoint public".

**Resolution is injected.** Deciding publicity needs DNS, and a module that
calls `socket` directly cannot be tested without a network. `HostResolver` is
the seam; `SystemHostResolver` is the only implementation that touches the
system, and it is the composition root's job to supply it.

The check is deliberately **conjunctive over all resolved addresses**: a host
that returns one global and one loopback address is refused, because an opponent
resolving it differently would reach the wrong place.
"""

import ipaddress
import socket
from typing import Protocol
from urllib.parse import urlsplit

from .public_endpoint_values import MCP_PATH, OwnPublicPeerEndpoint

_LOCAL_NAMES = frozenset({"localhost", "127.0.0.1", "::1", ""})


class HostResolver(Protocol):
    """Resolves a hostname to its literal addresses."""

    def resolve(self, host: str) -> tuple[str, ...]:
        """Return every address *host* resolves to, or `()` if it resolves to none."""
        ...


class SystemHostResolver:
    """The real resolver. The only place this module reaches the network."""

    def resolve(self, host: str) -> tuple[str, ...]:
        """Resolve through the system resolver, returning `()` on failure."""
        try:
            infos = socket.getaddrinfo(host, None, proto=socket.IPPROTO_TCP)
        except OSError:
            return ()
        return tuple(sorted({str(info[4][0]) for info in infos}))


def _is_public_address(literal: str) -> bool:
    try:
        address = ipaddress.ip_address(literal)
    except ValueError:
        return False
    return address.is_global


def is_public_endpoint(endpoint: OwnPublicPeerEndpoint, resolver: HostResolver) -> bool:
    """Whether *endpoint* satisfies FR-004 and FR-014 for counted play.

    Refuses, in order: a non-HTTPS scheme, embedded userinfo, any query or
    fragment, a path that is not the exact FastMCP path, a literally local host
    name, a host that resolves to nothing, and any resolved address that is not
    globally routable.
    """
    parts = urlsplit(endpoint.url)
    if parts.scheme != "https":
        return False
    if parts.username is not None or parts.password is not None:
        return False
    if parts.query or parts.fragment:
        return False
    if parts.path != MCP_PATH:
        return False
    host = (parts.hostname or "").lower()
    if host in _LOCAL_NAMES:
        return False
    addresses = resolver.resolve(host)
    if not addresses:
        return False
    return all(_is_public_address(address) for address in addresses)
