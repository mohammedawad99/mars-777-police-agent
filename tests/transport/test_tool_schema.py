"""The four public tools and their closed per-tool `kind` sets.

This is the file that would have caught the Stage-4E-R17 blocker: each tool's
schema restricts its **own** kind set, so a `commitment` cannot arrive at
`negotiate` and no receiver ever guesses from payload keys.
"""

import asyncio

import pytest
from fastmcp import Client
from fastmcp.exceptions import ToolError
from peer_recorder import RecordingOperations

from mars777_police.transport.envelopes import TOOL_KINDS
from mars777_police.transport.server import PEER_TOOLS, build_server


def schemas() -> dict[str, dict[str, object]]:
    async def run() -> dict[str, dict[str, object]]:
        async with Client(build_server(RecordingOperations())) as client:
            return {tool.name: tool.inputSchema for tool in await client.list_tools()}

    return asyncio.run(run())


def call(tool: str, arguments: dict[str, object]) -> object:
    async def run() -> object:
        async with Client(build_server(RecordingOperations())) as client:
            return (await client.call_tool(tool, arguments)).data

    return asyncio.run(run())


def test_the_server_exposes_exactly_the_four_peer_tools() -> None:
    assert sorted(schemas()) == sorted(PEER_TOOLS)
    assert sorted(PEER_TOOLS) == [
        "negotiate",
        "receive_control",
        "receive_turn",
        "submit_audit",
    ]


def test_no_debug_admin_or_role_specific_tool_leaked_onto_the_surface() -> None:
    for absent in ("debug", "admin", "police", "thief", "health", "ping"):
        assert not any(absent in name for name in schemas())


@pytest.mark.parametrize("tool", PEER_TOOLS)
def test_every_tool_takes_one_argument_named_request(tool: str) -> None:
    schema = schemas()[tool]
    assert list(schema["properties"]) == ["request"]
    assert schema["required"] == ["request"]


@pytest.mark.parametrize("tool", PEER_TOOLS)
def test_every_envelope_is_closed_with_kind_and_payload(tool: str) -> None:
    """`additionalProperties: false` reaches the published schema itself."""
    envelope = schemas()[tool]["properties"]["request"]
    variants = envelope.get("oneOf") or envelope.get("anyOf") or [envelope]
    for variant in variants:
        resolved = variant if "properties" in variant else envelope
        if "properties" in resolved:
            assert set(resolved["properties"]) <= {"kind", "payload"}


def test_each_tool_publishes_exactly_its_own_kind_vocabulary() -> None:
    published = {tool: set() for tool in PEER_TOOLS}
    for tool, schema in schemas().items():
        for found in _kinds(schema):
            published[tool].add(found)
    for tool, expected in TOOL_KINDS.items():
        assert published[tool] == set(expected), tool


def _kinds(node: object) -> set[str]:
    """Collect envelope `kind` tokens, never descending into a `payload`.

    The nested action tag is *also* spelled `kind` - `MOVE` / `BARRIER` inside a
    reveal - and it is a different discriminator at a different level. A walker
    that conflated the two would report a `receive_turn` vocabulary of five.
    """
    found: set[str] = set()
    if isinstance(node, dict):
        for key, value in node.items():
            if key == "payload":
                continue
            if key == "kind" and isinstance(value, dict):
                if "const" in value:
                    found.add(str(value["const"]))
                found.update(str(token) for token in value.get("enum", []))
            found |= _kinds(value)
    elif isinstance(node, list):
        for item in node:
            found |= _kinds(item)
    return found


def test_the_matrix_is_four_tools_and_nine_kinds_with_no_heartbeat() -> None:
    assert sum(len(kinds) for kinds in TOOL_KINDS.values()) == 9
    assert TOOL_KINDS["receive_control"] == ("result_agreement",)
    assert all("heartbeat" not in kinds for kinds in TOOL_KINDS.values())


@pytest.mark.parametrize(
    ("tool", "kind"),
    [
        ("negotiate", "commitment"),
        ("negotiate", "result_agreement"),
        ("receive_turn", "step0"),
        ("receive_turn", "audit_disclosure"),
        ("submit_audit", "reveal"),
        ("receive_control", "config_lock"),
    ],
)
def test_a_valid_kind_on_the_wrong_tool_is_refused(tool: str, kind: str) -> None:
    """No cross-tool redispatch: the tool's own enum never contained it."""
    with pytest.raises(ToolError):
        call(tool, {"request": {"kind": kind, "payload": {}}})


@pytest.mark.parametrize(
    "arguments",
    [
        {"request": {"kind": "unknown", "payload": {}}},
        {"request": {"kind": "Step0", "payload": {}}},
        {"request": {"kind": "step0 ", "payload": {}}},
        {"request": {"kind": "step0"}},
        {"request": {"payload": {}}},
        {"request": {"kind": "step0", "payload": {}, "version": 1}},
    ],
)
def test_every_malformed_envelope_is_refused(arguments: dict[str, object]) -> None:
    with pytest.raises(ToolError):
        call("negotiate", arguments)
