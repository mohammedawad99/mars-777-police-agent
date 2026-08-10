"""Success shapes and error identities, measured against the real framework.

Two rules carry the weight. Ordinary completion returns **no semantic value** -
never `accepted=true`. And a known application failure crosses carrying **exactly
its existing error identity**, so a lower-layer failure can never masquerade as
`reveal`'s legality `False`.
"""

import asyncio

import pytest
from fastmcp import Client, FastMCP
from fastmcp.exceptions import ToolError
from wire_probes import NegotiateEnvelope

from mars777_police.app.protocol_errors import StaleMessageError
from mars777_police.app.protocol_values import Sha256Digest

DIGEST = "a" * 64
ENVELOPE = {"kind": "step0", "payload": {}}


def server() -> FastMCP:
    mcp = FastMCP("results", strict_input_validation=True)

    @mcp.tool
    def completes(request: NegotiateEnvelope) -> None:
        return None

    @mcp.tool
    def legality(request: NegotiateEnvelope) -> bool:
        return bool(request.payload.get("legal"))

    @mcp.tool
    def digest(request: NegotiateEnvelope) -> str:
        return DIGEST

    @mcp.tool
    def fails(request: NegotiateEnvelope) -> None:
        raise ToolError(StaleMessageError.error_id)

    return mcp


def call(tool: str, payload: dict[str, object] | None = None) -> object:
    async def run() -> object:
        async with Client(server()) as client:
            envelope = {**ENVELOPE, "payload": payload or {}}
            return (await client.call_tool(tool, {"request": envelope})).data

    return asyncio.run(run())


def test_ordinary_completion_carries_no_semantic_value() -> None:
    assert call("completes") is None


def test_ordinary_completion_is_not_an_acceptance_flag() -> None:
    result = call("completes")
    assert result is not True
    assert not isinstance(result, dict)


def test_reveal_returns_an_exact_bool_in_both_directions() -> None:
    assert call("legality", {"legal": True}) is True
    assert call("legality", {"legal": False}) is False


def test_a_digest_crosses_as_exact_lowercase_hex_and_reconstructs() -> None:
    value = call("digest")
    assert value == DIGEST
    assert isinstance(value, str)
    assert Sha256Digest(str(value)).value == DIGEST


def test_a_known_failure_crosses_with_exactly_its_error_identity() -> None:
    """No prefix, no suffix, no Python exception text, no stack trace."""
    with pytest.raises(ToolError) as failure:
        call("fails")
    assert str(failure.value) == "E-PROTO-STALE"
    assert str(failure.value) == StaleMessageError.error_id


def test_the_identity_is_also_recoverable_without_raising() -> None:
    async def run() -> list[str]:
        async with Client(server()) as client:
            result = await client.call_tool("fails", {"request": ENVELOPE}, raise_on_error=False)
            assert result.is_error
            return [block.text for block in result.content if hasattr(block, "text")]

    assert asyncio.run(run()) == ["E-PROTO-STALE"]


def test_a_failure_never_arrives_as_a_legality_false() -> None:
    """The whole point: `False` means game-illegal and nothing else."""
    with pytest.raises(ToolError):
        call("fails")
    assert call("legality", {"legal": False}) is False


def test_no_exception_text_or_secret_leaks_through_the_error_channel() -> None:
    with pytest.raises(ToolError) as failure:
        call("fails")
    text = str(failure.value)
    for forbidden in ("Traceback", 'File "', "StaleMessageError", "key", "secret"):
        assert forbidden not in text
