"""The published tool surface, per profile, as a KIT implementation would read it.

A FastMCP tool schema is public interoperability surface: it is what a stranger
reads to learn how to call us. So the assertions below query the **served**
surface rather than a Python signature, and they assert one profile's schema
per process. There is deliberately no schema carrying both families: a process
that published a strict and a KIT argument shape on one tool would be asking a
peer to guess which one this run means.

Mode is chosen out of band, before the server is built. Nothing here negotiates
it, infers it from a payload, or falls back from one to the other.
"""

import asyncio

import pytest
from fastmcp import Client
from kit_session_support import kit_context, kit_server
from kit_wire_vectors import ARGUMENT_NAMES, PINNED_SCHEMAS, TOOLS
from peer_recorder import RecordingOperations

from mars777_police.transport.server import PEER_TOOLS, build_server
from mars777_police.transport.transport_profiles import TransportEnvelopeProfile


def schemas(server: object) -> dict[str, dict[str, object]]:
    """The tool schemas exactly as a peer's `tools/list` receives them."""

    async def run() -> dict[str, dict[str, object]]:
        async with Client(server) as client:
            return {tool.name: tool.inputSchema for tool in await client.list_tools()}

    return asyncio.run(run())


def test_the_kit_surface_publishes_the_four_pinned_tool_names_and_no_fifth() -> None:
    published = schemas(kit_server(RecordingOperations(), kit_context()))

    assert sorted(published) == sorted(TOOLS)


@pytest.mark.parametrize("tool", TOOLS)
def test_each_kit_tool_takes_exactly_its_pinned_argument_name(tool: str) -> None:
    published = schemas(kit_server(RecordingOperations(), kit_context()))
    schema = published[tool]

    assert list(schema["properties"]) == [ARGUMENT_NAMES[tool]]
    assert schema["required"] == [ARGUMENT_NAMES[tool]]


@pytest.mark.parametrize("tool", TOOLS)
def test_each_kit_argument_is_the_free_form_json_object_the_kit_publishes(tool: str) -> None:
    """`message: dict` on the pinned wire - the shape is checked inside, not in the schema."""
    schema = schemas(kit_server(RecordingOperations(), kit_context()))[tool]
    argument = schema["properties"][ARGUMENT_NAMES[tool]]

    assert argument["type"] == "object"
    assert "$ref" not in argument


def test_the_strict_surface_is_untouched_by_the_kit_profile_existing() -> None:
    published = schemas(build_server(RecordingOperations()))

    assert sorted(published) == sorted(PEER_TOOLS)
    for tool in PEER_TOOLS:
        assert list(published[tool]["properties"]) == ["request"]


def test_the_two_surfaces_share_their_names_and_share_no_argument_shape() -> None:
    kit = schemas(kit_server(RecordingOperations(), kit_context()))
    strict = schemas(build_server(RecordingOperations()))

    assert sorted(kit) == sorted(strict)
    for tool in strict:
        assert list(kit[tool]["properties"]) != list(strict[tool]["properties"])


def test_no_tool_schema_ever_carries_both_argument_families() -> None:
    for server in (
        kit_server(RecordingOperations(), kit_context()),
        build_server(RecordingOperations()),
    ):
        for tool, schema in schemas(server).items():
            names = set(schema["properties"])
            assert not ({"request"} <= names and {"message", "payload"} & names), tool


def test_the_profile_selects_the_surface_and_is_a_construction_argument() -> None:
    """Pre-boot, by the caller - never negotiated by the messages it governs."""
    server = build_server(
        RecordingOperations(),
        profile=TransportEnvelopeProfile.KIT_EXTERNAL,
        context=kit_context(),
    )

    assert list(schemas(server)["submit_audit"]["properties"]) == ["payload"]


STRICTNESS = {"additionalProperties": False}
"""Our one published difference: we refuse an unknown *argument*, they ignore it."""


@pytest.mark.parametrize("tool", TOOLS)
def test_our_published_schema_matches_the_pinned_peers_own(tool: str) -> None:
    """The mechanical comparison: can a KIT implementation know how to call us?

    Argument name, requiredness and the free-form object are byte-identical to
    what the pinned peer publishes from its own FastMCP major. The single
    difference is at the *tool argument* level: `strict_input_validation` closes
    the argument object, so a caller sending a second, unknown argument is
    refused rather than ignored. The extension seam the kit actually defines is
    one level down, **inside** `message`, and that stays open - which is what
    the pinned unknown-key row exercises.
    """
    published = schemas(kit_server(RecordingOperations(), kit_context()))[tool]

    assert published == PINNED_SCHEMAS[tool] | STRICTNESS
    assert published["properties"][ARGUMENT_NAMES[tool]]["additionalProperties"] is True
