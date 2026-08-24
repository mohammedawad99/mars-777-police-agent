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

from mars777_police.app.counted_mode import counted
from mars777_police.app.kit_handoff import SeriesHandoff
from mars777_police.app.kit_messages import (
    KitRole,
)
from mars777_police.app.protocol_errors import StaleMessageError
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


def test_a_rehearsal_keeps_no_contribution_entry_and_does_not_kill_its_backend() -> None:
    """The friendly regression: publishing an entry must not refuse in a rehearsal.

    A friendly has no Step-0, so the gateway holds no merged declaration. The
    backend publishes a contribution entry after every sub-game regardless, and
    admitting one against an absent declaration raised `E-PROTO-STALE` - which
    reached the backend as a tool error and killed it after sub-game one, before
    it could signal settlement. A run that owes no result keeps no entry.
    """
    held, _ = gateway_pair()
    assert held.counted.is_counted is False
    assert held.declaration is None

    held.contribute_entry(1, KitRole.POLICE, "a" * 40, 0)

    assert held.contributed.entries == {}
    assert held.contributed.complete is False


def test_a_counted_run_still_refuses_an_entry_with_no_declaration() -> None:
    """The counted guard is untouched: a run that owes a result must not skip."""
    held, _ = gateway_pair()
    held.counted = counted()

    try:
        held.contribute_entry(1, KitRole.POLICE, "a" * 40, 0)
    except StaleMessageError as failure:
        assert "declaration" in str(failure)
    else:  # pragma: no cover - the refusal is the point of the test
        raise AssertionError("a counted entry with no declaration was admitted")


def test_the_greeting_answer_names_us_so_a_peer_derives_the_same_game_id() -> None:
    """A peer learns our identity from the negotiate answer or from nowhere.

    The pinned answer is a bare `{"ok": true}`. We accept `group_id` from a peer
    and returned none, so a correct peer fell back to its own slug and derived
    `<them>-vs-opponent` - a different `game_id`, which is the first key of both
    the consensus document and `RESULT_APPROVAL_CORE`. Every digest of that
    series was void against ours, in both directions.
    """
    held, _ = gateway_pair()
    held.group_id = "MaRs-777"

    answer = asyncio.run(held.negotiate(greeting(role="thief", sub_game_number=1)))

    assert answer["ok"] is True
    assert answer["group_id"] == "MaRs-777"


def test_an_unconfigured_gateway_still_answers_exactly_the_pinned_object() -> None:
    """No group_id means silence, never an empty slug a peer would adopt."""
    held, _ = gateway_pair()
    assert held.group_id == ""

    answer = asyncio.run(held.negotiate(greeting(role="thief", sub_game_number=1)))

    assert answer == {"ok": True}
