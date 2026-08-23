"""A held backend session that dies, and the one thing that may be retried.

Holding one session per role is deliberate - Stage 4E measured thirty operations
each opening their own session failing from the twenty-first onward - but a cache
that never reopens turns a single dropped connection into a backend that is
unreachable for the rest of the series.

The line these tests defend: a **transport** failure is a broken wire and a fresh
session is the repair; a **backend refusal** is a decision, and retrying it would
only hide it.
"""

import asyncio

import pytest

from mars777_police.app.kit_messages import KitRole
from mars777_police.app.protocol_errors import StaleMessageError
from mars777_police.transport.kit_backend_routes import KitBackendRoutes
from mars777_police.transport.wire_errors import TransportFailureError


class Session:
    """One stand-in session: it fails while *failing*, and counts every call."""

    def __init__(self, failure: Exception | None) -> None:
        self.failure, self.calls, self.closed = failure, 0, False

    async def invoke(self, tool: str, arguments: dict[str, object]) -> None:
        self.calls += 1
        if self.failure is not None:
            raise self.failure

    async def __aexit__(self, kind: object, value: object, traceback: object) -> None:
        self.closed = True


class Routes(KitBackendRoutes):
    """The real forwarder, over sessions this test hands out in order."""

    def __init__(self, sessions: list[Session]) -> None:
        super().__init__({KitRole.POLICE: "http://127.0.0.1:1/mcp"}, 1.0)
        self.queue, self.opened = sessions, []

    async def _client(self, role: KitRole) -> object:  # type: ignore[override]
        held = self.clients.get(role)
        if held is None:
            held = self.queue.pop(0)
            self.clients[role] = held  # type: ignore[assignment]
            self.opened.append(held)
        return held


def forward(routes: Routes) -> object:
    return routes.forwarders()[KitRole.POLICE]("negotiate", {})


def test_a_healthy_session_is_used_once_and_held() -> None:
    live = Session(None)
    routes = Routes([live, Session(None)])
    asyncio.run(forward(routes))
    asyncio.run(forward(routes))
    assert live.calls == 2
    assert routes.opened == [live]


def test_a_dead_session_is_replaced_and_the_call_succeeds() -> None:
    """The defect: without this the backend stays unreachable for the series."""
    dead, fresh = Session(TransportFailureError("gone")), Session(None)
    routes = Routes([dead, fresh])
    asyncio.run(forward(routes))
    assert dead.calls == 1
    assert fresh.calls == 1
    assert dead.closed


def test_a_backend_refusal_is_never_retried() -> None:
    """A decision, not a broken wire - retrying it would only hide it."""
    refusing, unused = Session(StaleMessageError("E-PROTO-STALE")), Session(None)
    routes = Routes([refusing, unused])
    with pytest.raises(StaleMessageError):
        asyncio.run(forward(routes))
    assert refusing.calls == 1
    assert unused.calls == 0
    assert not refusing.closed


def test_a_second_transport_failure_propagates() -> None:
    """Exactly one repair. A wire that is still broken is reported, not looped."""
    routes = Routes(
        [Session(TransportFailureError("gone")), Session(TransportFailureError("gone"))]
    )
    with pytest.raises(TransportFailureError):
        asyncio.run(forward(routes))
    assert len(routes.opened) == 2


def test_a_session_that_cannot_close_still_gets_replaced() -> None:
    """A dead session may fail to close; it is going away either way."""

    class Stubborn(Session):
        async def __aexit__(self, kind: object, value: object, traceback: object) -> None:
            raise RuntimeError("already gone")

    routes = Routes([Stubborn(TransportFailureError("gone")), Session(None)])
    asyncio.run(forward(routes))
    assert routes.opened[1].calls == 1


def test_discarding_a_role_that_was_never_opened_is_harmless() -> None:
    """A forwarder can fail before any session existed; there is nothing to close."""
    routes = KitBackendRoutes({KitRole.POLICE: "http://127.0.0.1:1/mcp"}, 1.0)
    asyncio.run(routes._discard(KitRole.POLICE))
    assert routes.clients == {}
