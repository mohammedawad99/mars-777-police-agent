"""The group gateway over a real client: what it publishes, routes and refuses.

One stable public surface in front of two private backends. These run against a
real client rather than a stub, because the thing under test is the forwarding
itself - including that a refusal crosses as its own error identity instead of
arriving as the gateway's.
"""

import asyncio

from fastmcp import Client
from kit_backend_doubles import _wire_turn
from test_kit_gateway import greeting

from mars777_police.app.kit_handoff import SeriesHandoff
from mars777_police.app.kit_messages import (
    KitRole,
)
from mars777_police.transport.kit_gateway import KitGroupGateway
from mars777_police.transport.kit_gateway_server import (
    ADMIN_TOOLS,
    GATEWAY_TOOLS,
    build_gateway_admin,
    build_gateway_tools,
)


def gateway_pair() -> tuple[KitGroupGateway, dict[str, list[str]]]:
    seen: dict[str, list[str]] = {"police": [], "thief": []}

    def route(side: str):
        async def forward(tool: str, arguments: dict[str, object]) -> None:
            seen[side].append(tool)

        return forward

    held = KitGroupGateway(
        handoff=SeriesHandoff(KitRole.POLICE),
        routes={KitRole.POLICE: route("police"), KitRole.THIEF: route("thief")},
        deadline=1.0,
    )
    return held, seen


def test_the_gateway_publishes_the_pinned_surface_and_a_private_one() -> None:
    held, _ = gateway_pair()

    async def run() -> tuple[list[str], list[str]]:
        async with Client(build_gateway_tools(held)) as public:
            names = [tool.name for tool in await public.list_tools()]
        async with Client(build_gateway_admin(held)) as admin:
            private = [tool.name for tool in await admin.list_tools()]
        return names, private

    names, private = asyncio.run(run())

    assert sorted(names) == sorted(GATEWAY_TOOLS)
    assert private == list(ADMIN_TOOLS)


def test_every_gateway_tool_routes_and_acknowledges_over_a_real_client() -> None:
    held, seen = gateway_pair()

    async def run() -> list[object]:
        async with (
            Client(build_gateway_tools(held)) as public,
            Client(build_gateway_admin(held)) as admin,
        ):
            answers = [
                (
                    await public.call_tool(
                        "negotiate", {"message": greeting(role="thief", sub_game_number=1)}
                    )
                ).data,
                (await public.call_tool("receive_turn", {"message": _wire_turn()})).data,
                (
                    await public.call_tool(
                        "receive_control", {"message": {"kind": "status", "sender": "thief"}}
                    )
                ).data,
                (
                    await public.call_tool(
                        "submit_audit",
                        {"payload": {"sender": "thief", "records": [], "result_claim": "survival"}},
                    )
                ).data,
                (await admin.call_tool("sub_game_settled", {"sub_game": 1})).data,
            ]
            return answers

    answers = asyncio.run(run())

    assert answers == [{"ok": True}] * 5
    assert seen["police"] == ["negotiate", "receive_turn", "receive_control", "submit_audit"]


def test_a_refusal_crosses_the_gateway_as_its_own_error_identity() -> None:
    from fastmcp.exceptions import ToolError

    held, _ = gateway_pair()

    async def run() -> None:
        async with Client(build_gateway_tools(held)) as public:
            await public.call_tool(
                "negotiate", {"message": greeting(role="police", sub_game_number=1)}
            )

    try:
        asyncio.run(run())
    except ToolError as failure:
        assert "E-PROTO-STALE" in str(failure)
    else:  # pragma: no cover - the refusal is the point of the test
        raise AssertionError("a role collision was not refused")
