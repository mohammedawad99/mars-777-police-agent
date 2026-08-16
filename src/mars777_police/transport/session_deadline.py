"""Keeping a held session's response deadline current after the lock.

The peer session is opened during startup, before Step-0 and necessarily
before any configuration is locked - a client that demanded a locked config
could never make the calls that produce one. The HTTP client built at that
moment took the pre-lock window as its read timeout and kept it, so the agreed
`response_timeout_sec` governed the MCP call while the socket read underneath
still gave up on the old bound.

**The number becomes a question.** `httpx` stamps each request with the
client's `timeout` property when `build_request` runs, so a client that
answers that property from the live authority gives every request built after
the lock the deadline the peers agreed - without reopening anything. The held
session, its connection pool and its identity are untouched, which matters:
one session per peer lifecycle is a measured choice, not an incidental one.

**Only the response component moves.** `response_timeout_sec` is a response
deadline. Connect, write and pool belong to the transport that already chose
them and are passed through exactly as given; widening them for symmetry would
be this project taking ownership of values it never negotiated.

The seam is FastMCP's own documented `httpx_client_factory`, so nothing here
patches, vendors or reaches into a library's private state.
"""

from collections.abc import Callable
from typing import Any

import httpx
from fastmcp.client.transports import StreamableHttpTransport

from ..app.peer_supervision import PeerDeadline


class DeadlineClient(httpx.AsyncClient):
    """An `AsyncClient` whose read budget is asked for, not remembered."""

    def __init__(self, deadline: PeerDeadline, **kwargs: Any) -> None:
        self._peer_deadline = deadline
        super().__init__(**kwargs)

    @property
    def timeout(self) -> httpx.Timeout:
        """The client default a request built now would be stamped with."""
        given = httpx.AsyncClient.timeout.fget(self)  # type: ignore[attr-defined]
        return httpx.Timeout(
            connect=given.connect,
            read=self._peer_deadline.seconds(),
            write=given.write,
            pool=given.pool,
        )

    @timeout.setter
    def timeout(self, value: Any) -> None:
        httpx.AsyncClient.timeout.fset(self, value)  # type: ignore[attr-defined]


def session_transport(url: str, deadline: PeerDeadline) -> StreamableHttpTransport:
    """The peer transport, wired to answer *deadline* for every new request."""
    return StreamableHttpTransport(url, httpx_client_factory=deadline_factory(deadline))


def deadline_factory(deadline: PeerDeadline) -> Callable[..., httpx.AsyncClient]:
    """A FastMCP client factory whose clients follow *deadline*.

    Every keyword FastMCP supplies is passed through untouched, so the headers,
    auth and redirect behaviour the transport chose remain its own.
    """

    def build(**kwargs: Any) -> httpx.AsyncClient:
        return DeadlineClient(deadline, **kwargs)

    return build
