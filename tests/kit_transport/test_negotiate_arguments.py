"""The three agreed spellings of `negotiate`, and what each one means.

The pairing froze `{"tool":"negotiate","kind":"step0"}` and never said whether
`kind` and `payload` were top-level MCP arguments or nested inside `request`.
Both teams implemented to the letter and to different shapes; a live rehearsal
Step-0 was rejected at input validation *before* authentication - no HMAC
checked, no sub-game started, no artifact written. Neither reading was wrong, so
both are accepted and this file is what keeps that true.
"""

import asyncio
from typing import Any

import pytest
from fastmcp import Client
from fastmcp.exceptions import ToolError

from mars777_police.app.kit_handoff import SeriesHandoff
from mars777_police.app.kit_messages import KitRole
from mars777_police.app.protocol_errors import MalformedMessageError
from mars777_police.transport.kit_gateway import KitGroupGateway
from mars777_police.transport.kit_gateway_server import build_gateway_tools
from mars777_police.transport.negotiate_arguments import step0_arguments

EXCHANGE: dict[str, Any] = {"declaration": {"game_id": "g"}, "auth": {"value": "v"}}


def test_a_greeting_is_not_a_step0() -> None:
    assert step0_arguments({"terms": {}}, None, None, None) is None


def test_the_agreed_cross_team_form_is_accepted() -> None:
    """Top-level `kind`/`payload` - the shape the peer's runner sends."""
    assert step0_arguments(None, None, "step0", EXCHANGE) == EXCHANGE


def test_our_native_envelope_is_still_accepted() -> None:
    """`request={kind,payload}` - what this project's own client emits."""
    assert step0_arguments(None, {"kind": "step0", "payload": EXCHANGE}, None, None) == EXCHANGE


def test_both_spellings_yield_the_identical_payload() -> None:
    """One meaning, two spellings: the receiver must not be able to tell them apart."""
    top = step0_arguments(None, None, "step0", EXCHANGE)
    nested = step0_arguments(None, {"kind": "step0", "payload": EXCHANGE}, None, None)
    assert top == nested == EXCHANGE


def test_mixing_the_two_spellings_is_refused() -> None:
    """One call states one shape; a mixed call names two and means neither."""
    with pytest.raises(MalformedMessageError, match="one call states one shape"):
        step0_arguments(None, {"kind": "step0", "payload": EXCHANGE}, "step0", EXCHANGE)


def test_half_a_top_level_call_is_refused() -> None:
    with pytest.raises(MalformedMessageError, match="names nothing"):
        step0_arguments(None, None, "step0", None)
    with pytest.raises(MalformedMessageError, match="names nothing"):
        step0_arguments(None, None, None, EXCHANGE)


@pytest.mark.parametrize("kind", ["config_proposal", "config_lock", "turn", ""])
def test_only_step0_is_carried_on_the_public_route(kind: str) -> None:
    """The other internal kinds were never exposed publicly and are not now."""
    with pytest.raises(MalformedMessageError, match="not exposed here"):
        step0_arguments(None, None, kind, EXCHANGE)
    with pytest.raises(MalformedMessageError, match="not exposed here"):
        step0_arguments(None, {"kind": kind, "payload": EXCHANGE}, None, None)


def test_a_malformed_request_envelope_is_refused() -> None:
    for broken in ({}, {"kind": "step0"}, {"kind": 1, "payload": {}}, {"payload": {}}):
        with pytest.raises(MalformedMessageError):
            step0_arguments(None, broken, None, None)


def gateway() -> KitGroupGateway:
    return KitGroupGateway(handoff=SeriesHandoff(KitRole.POLICE), routes={}, deadline=1.0)


def test_the_public_schema_advertises_all_three_forms() -> None:
    """What the peer queries with `list_tools` before trusting the route."""

    async def run() -> list[str]:
        async with Client(build_gateway_tools(gateway(), step0=lambda p: none())) as c:
            for t in await c.list_tools():
                if t.name == "negotiate":
                    return sorted(t.inputSchema.get("properties", {}))
        return []

    async def none() -> None:
        return None

    assert asyncio.run(run()) == ["kind", "message", "payload", "request"]


def test_a_top_level_step0_reaches_the_receiver_over_a_real_session() -> None:
    """End to end through MCP: the exact call the peer's runner makes."""
    seen: list[dict[str, Any]] = []

    async def receive(payload: dict[str, Any]) -> None:
        seen.append(payload)

    async def run() -> None:
        async with Client(build_gateway_tools(gateway(), step0=receive)) as c:
            await c.call_tool("negotiate", {"kind": "step0", "payload": EXCHANGE})

    asyncio.run(run())
    assert seen == [EXCHANGE]


def test_a_route_with_no_receiver_refuses_step0_rather_than_dropping_it() -> None:
    """Fail closed: a counted series must not proceed on a Step-0 that went nowhere."""

    async def run() -> None:
        async with Client(build_gateway_tools(gateway(), step0=None)) as c:
            await c.call_tool("negotiate", {"kind": "step0", "payload": EXCHANGE})

    with pytest.raises(ToolError, match=r"E-LOCAL-DEFECT|nowhere to go"):
        asyncio.run(run())


def test_negotiate_with_no_arguments_at_all_is_refused() -> None:
    async def run() -> None:
        async with Client(build_gateway_tools(gateway(), step0=None)) as c:
            await c.call_tool("negotiate", {})

    with pytest.raises(ToolError):
        asyncio.run(run())
