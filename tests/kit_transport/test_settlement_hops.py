"""The last hops of the settlement path, each exercised against a real object.

Small pieces, but every one of them sits between a played series and a settled
one - and a series that plays perfectly and settles on nothing is scored the
same as one that was never played.
"""

import asyncio
from typing import Any

import pytest
from fastmcp import FastMCP

from mars777_police.app.kit_friendly import KitFriendlySession
from mars777_police.app.kit_messages import KitAuditReveal, KitResultClaim, KitRole
from mars777_police.app.run_class import RunClassification
from mars777_police.transport.kit_admin_client import KitAdminClient
from mars777_police.transport.kit_backend_routes import KitBackendRoutes
from mars777_police.transport.peer_transport import FastMcpPeerTransport

DIGEST = "33f1b2032e8ce87e8bd99de82aac5ebb29943571e2ae583ce4ee2d22f2eeaf1c"
ENVELOPE: dict[str, Any] = {
    "sender": "thief",
    "result_claim": "series_consensus",
    "records": [],
    "consensus_sha": DIGEST,
}


def session() -> KitFriendlySession:
    return KitFriendlySession(RunClassification.friendly(kit_terms_agreement=True))


def test_taking_the_settlement_never_blocks() -> None:
    """The exchange polls, because it must keep resending while it waits."""
    live = session()
    assert live.take_settlement() is None
    arrived = KitAuditReveal(KitRole.POLICE, (), KitResultClaim.SERIES_CONSENSUS, DIGEST)
    live.deliver_audit(arrived)
    assert live.take_settlement() is arrived
    assert live.take_settlement() is arrived


def test_the_settlement_goes_out_as_raw_arguments() -> None:
    """Not through the disclosure encoder: this carries a digest, not a chain."""
    sent: list[tuple[str, dict[str, object]]] = []

    class Client:
        profile = None

        async def invoke(self, tool: str, request: dict[str, object]) -> None:
            sent.append((tool, request))

    transport = FastMcpPeerTransport(Client())  # type: ignore[arg-type]
    assert asyncio.run(transport.send_settlement(ENVELOPE)) is True
    assert sent == [("submit_audit", {"payload": ENVELOPE})]


def test_a_refused_settlement_send_does_not_end_the_exchange() -> None:
    """A peer still finishing its last sub-game refuses; the cadence retries."""

    class Refusing:
        profile = None

        async def invoke(self, tool: str, request: dict[str, object]) -> None:
            raise RuntimeError("the peer is not ready for a settlement yet")

    transport = FastMcpPeerTransport(Refusing())  # type: ignore[arg-type]
    assert asyncio.run(transport.send_settlement(ENVELOPE)) is False, (
        "a refusal must be reported, not hidden: the exchange needs to know"
        " our own envelope has not landed yet"
    )


def test_a_group_that_answers_with_something_other_than_rows_is_refused() -> None:
    """A named refusal, rather than iterating whatever arrived."""
    server: FastMCP = FastMCP("wrong-shape", strict_input_validation=True)

    @server.tool
    async def series_rows() -> dict[str, str]:
        return {"rows": "not a list"}

    async def run() -> None:
        async with KitAdminClient(server) as client:  # type: ignore[arg-type]
            await client.series_rows()

    with pytest.raises(RuntimeError, match="not a list of rows"):
        asyncio.run(run())


def test_a_forwarder_that_succeeds_first_time_never_reopens() -> None:
    """The repair path must not run for a healthy session."""
    opened: list[object] = []

    class Session:
        async def invoke(self, tool: str, arguments: dict[str, object]) -> None:
            return None

    class Routes(KitBackendRoutes):
        async def _client(self, role: KitRole) -> object:  # type: ignore[override]
            held = self.clients.get(role)
            if held is None:
                held = Session()
                self.clients[role] = held  # type: ignore[assignment]
                opened.append(held)
            return held

    routes = Routes({KitRole.POLICE: "http://127.0.0.1:1/mcp"}, 1.0)
    asyncio.run(routes.forwarders()[KitRole.POLICE]("negotiate", {}))
    asyncio.run(routes.forwarders()[KitRole.POLICE]("negotiate", {}))
    assert len(opened) == 1
