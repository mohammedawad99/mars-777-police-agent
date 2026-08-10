"""The frozen envelope, enforced by the real framework rather than by prose.

`{kind, payload}` with both members required, a closed per-tool `kind`, and no
extra member. Stage 4E-R17 could not dispatch without this, and §F forbids
guessing which payload keys happen to be present.
"""

import asyncio

import pytest
from fastmcp import Client, FastMCP
from fastmcp.exceptions import ToolError
from wire_probes import TOOL_KINDS, NegotiateEnvelope


def server() -> FastMCP:
    mcp = FastMCP("envelope", strict_input_validation=True)

    @mcp.tool
    def negotiate(request: NegotiateEnvelope) -> None:
        return None

    return mcp


def call(arguments: dict[str, object]) -> object:
    async def run() -> object:
        async with Client(server()) as client:
            return (await client.call_tool("negotiate", arguments)).data

    return asyncio.run(run())


def schema() -> dict[str, object]:
    async def run() -> dict[str, object]:
        async with Client(server()) as client:
            return (await client.list_tools())[0].inputSchema

    return asyncio.run(run())


def test_the_tool_takes_exactly_one_argument_named_request() -> None:
    generated = schema()
    assert list(generated["properties"]) == ["request"]
    assert generated["required"] == ["request"]
    assert generated["additionalProperties"] is False


def test_the_envelope_has_exactly_kind_and_payload_both_required() -> None:
    envelope = schema()["properties"]["request"]
    assert sorted(envelope["properties"]) == ["kind", "payload"]
    assert sorted(envelope["required"]) == ["kind", "payload"]
    assert envelope["additionalProperties"] is False


def test_the_kind_vocabulary_is_closed_in_the_published_schema() -> None:
    kind = schema()["properties"]["request"]["properties"]["kind"]
    assert kind["enum"] == list(TOOL_KINDS["negotiate"])


def test_a_valid_envelope_is_accepted_and_completes_with_no_value() -> None:
    assert call({"request": {"kind": "step0", "payload": {}}}) is None


@pytest.mark.parametrize(
    ("arguments", "reason"),
    [
        ({"request": {"kind": "unknown", "payload": {}}}, "unknown kind"),
        ({"request": {"kind": "commitment", "payload": {}}}, "kind of another tool"),
        ({"request": {"kind": "Step0", "payload": {}}}, "case-folded kind"),
        ({"request": {"kind": "step0 ", "payload": {}}}, "untrimmed kind"),
        ({"request": {"kind": 5, "payload": {}}}, "kind not a string"),
        ({"request": {"kind": "step0"}}, "missing payload"),
        ({"request": {"payload": {}}}, "missing kind"),
        ({"request": {"kind": "step0", "payload": {}, "version": 1}}, "extra member"),
        ({"request": {"kind": "step0", "payload": []}}, "payload not an object"),
    ],
)
def test_every_malformed_envelope_is_refused(arguments: dict[str, object], reason: str) -> None:
    with pytest.raises(ToolError):
        call(arguments)


def test_no_heartbeat_kind_exists() -> None:
    """`receive_control` carries `result_agreement` only, by decision."""
    assert TOOL_KINDS["receive_control"] == ("result_agreement",)
    assert all("heartbeat" not in kinds for kinds in TOOL_KINDS.values())


def test_the_matrix_is_four_tools_and_nine_kinds() -> None:
    assert sorted(TOOL_KINDS) == [
        "negotiate",
        "receive_control",
        "receive_turn",
        "submit_audit",
    ]
    assert sum(len(kinds) for kinds in TOOL_KINDS.values()) == 9
