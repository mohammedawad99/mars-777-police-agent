"""What the backend and the gateway refuse, and how the refusal crosses.

A refusal has to arrive as its **own** error identity: a peer that is told
somebody else's failure cannot act on it, and a defect that arrives wearing a
protocol error survives to the next stage. These pin the translation at both
surfaces the operator actually exposes.
"""

import asyncio

import pytest
from fastmcp import Client
from fastmcp.exceptions import ToolError
from kit_backend_builders import backend
from kit_wire_vectors import COMMIT

from mars777_police.__main__ import ROLE
from mars777_police.app.kit_handoff import SeriesHandoff
from mars777_police.app.kit_messages import KitRole
from mars777_police.app.kit_payload import PeerPayload
from mars777_police.app.kit_session import KitSessionContext
from mars777_police.app.protocol_errors import LocalDefectError
from mars777_police.app.run_class import RunClassification
from mars777_police.transport.kit_gateway import KitGroupGateway
from mars777_police.transport.kit_gateway_server import build_gateway_admin, build_gateway_tools

OURS = KitRole(ROLE.value)


def test_a_backend_refuses_a_run_class_that_is_not_a_friendly() -> None:
    held = backend(KitRole.POLICE)
    held.friendly.classification = RunClassification.counted(keyed_auth_satisfied=True)

    with pytest.raises(LocalDefectError):
        held.__post_init__()


def test_a_backend_refuses_a_context_carrying_the_other_role() -> None:
    held = backend(KitRole.POLICE)
    other = KitRole.THIEF if OURS is KitRole.POLICE else KitRole.POLICE
    held.context = KitSessionContext("MaRs-777", other, PeerPayload({"a": 1}), 1)

    with pytest.raises(LocalDefectError):
        held.__post_init__()


def test_every_gateway_tool_translates_a_refusal_into_its_error_identity() -> None:
    held = KitGroupGateway(handoff=SeriesHandoff(KitRole.POLICE), routes={}, deadline=0.2)
    turn = {
        "step": 1,
        "sender": "thief",
        "hint": "x",
        "smell_grid": {"0,0": 0.5},
        "commit": COMMIT,
        "timestamp": "2026-08-18T00:00:00Z",
    }

    async def run() -> list[str]:
        failures: list[str] = []
        async with Client(build_gateway_tools(held)) as public:
            for tool, body in (
                ("receive_turn", {"message": turn}),
                (
                    "submit_audit",
                    {"payload": {"sender": "thief", "records": [], "result_claim": "survival"}},
                ),
                ("receive_control", {"message": {"kind": "status", "sender": "thief"}}),
                (
                    "negotiate",
                    {
                        "message": {
                            "terms": {},
                            "nonce": "a",
                            "signature": "b",
                            "group_id": "g",
                            "sub_game_number": 4,
                        }
                    },
                ),
            ):
                try:
                    await public.call_tool(tool, body)
                except ToolError as failure:
                    failures.append(str(failure))
        return failures

    assert len(asyncio.run(run())) == 4


def test_the_admin_surface_refuses_a_settlement_for_another_sub_game() -> None:
    held = KitGroupGateway(handoff=SeriesHandoff(KitRole.POLICE), routes={}, deadline=0.2)

    async def run() -> str:
        async with Client(build_gateway_admin(held)) as admin:
            try:
                await admin.call_tool("sub_game_settled", {"sub_game": 5})
            except ToolError as failure:
                return str(failure)
        return ""

    assert "E-PROTO-STALE" in asyncio.run(run())
