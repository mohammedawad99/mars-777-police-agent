"""`Decimal("0.10")` must survive the wire, or two honest peers refuse each other.

The measured failure this contract exists to prevent: a `Decimal`-annotated
parameter handed the JSON **number** `0.10` arrives as `Decimal('0.1')`. That is
a silent lexical loss, it changes `config_sha256`, and no amount of care further
down the stack recovers it. Canonical **text** is therefore the wire form.
"""

import asyncio
from dataclasses import replace
from decimal import Decimal

import pytest
from fastmcp import Client, FastMCP
from fastmcp.exceptions import ToolError
from r16_builders import config
from wire_probes import ConfigProposalEnvelope

from mars777_police.domain.config_league_sections import PheromoneTerms
from mars777_police.protocol.canonical import canonical_json_bytes, decimal_text
from mars777_police.protocol.config_lock import config_sha256
from mars777_police.protocol.config_projection import config_core


def server() -> FastMCP:
    mcp = FastMCP("decimal", strict_input_validation=True)

    @mcp.tool
    def negotiate(request: ConfigProposalEnvelope) -> str:
        terms = PheromoneTerms(
            Decimal(request.payload.pheromone_center_intensity),
            Decimal(request.payload.pheromone_decay),
            request.payload.pheromone_grid_size,
        )
        return config_sha256(replace(config(), pheromones=terms)).value

    return mcp


def send(payload: dict[str, object]) -> str:
    async def run() -> str:
        async with Client(server()) as client:
            result = await client.call_tool(
                "negotiate", {"request": {"kind": "config_proposal", "payload": payload}}
            )
            return str(result.data)

    return asyncio.run(run())


def wire_payload() -> dict[str, object]:
    terms = config().pheromones
    return {
        "pheromone_center_intensity": decimal_text(terms.pheromone_center_intensity),
        "pheromone_decay": decimal_text(terms.pheromone_decay),
        "pheromone_grid_size": terms.pheromone_grid_size,
    }


def test_the_wire_form_is_canonical_decimal_text() -> None:
    payload = wire_payload()
    assert payload["pheromone_decay"] == "0.10"
    assert payload["pheromone_center_intensity"] == "0.9"


def test_the_config_digest_survives_the_real_framework_boundary() -> None:
    assert send(wire_payload()) == config_sha256(config()).value


def test_the_canonical_bytes_still_carry_a_bare_json_number() -> None:
    """The transport uses text; the canonical layer is untouched."""
    raw = canonical_json_bytes(config_core(config()))
    assert b'"pheromone_decay":0.10' in raw
    assert b'"pheromone_decay":"0.10"' not in raw


def test_a_trailing_zero_is_numerically_equal_and_lexically_decisive() -> None:
    """The exact subtlety this whole contract turns on.

    `Decimal("0.10") == Decimal("0.1")` is **True** - they are the same number.
    Their canonical *text* differs, the canonical config bytes therefore differ,
    and so does `config_sha256`. An equality check would never have caught a
    lossy wire; only the digest does.
    """
    assert Decimal("0.10") == Decimal("0.1")
    assert decimal_text(Decimal("0.10")) != decimal_text(Decimal("0.1"))
    assert send(wire_payload()) != send({**wire_payload(), "pheromone_decay": "0.1"})


@pytest.mark.parametrize(
    ("value", "reason"),
    [
        (0.10, "json float"),
        (10, "json integer"),
        ("1E-1", "scientific notation"),
        (" 0.10", "leading whitespace"),
        ("0.10 ", "trailing whitespace"),
        ("+0.10", "explicit plus"),
        ("0,10", "locale comma"),
        (None, "null"),
    ],
)
def test_every_lossy_or_ambiguous_decimal_form_is_refused(value: object, reason: str) -> None:
    with pytest.raises(ToolError):
        send({**wire_payload(), "pheromone_decay": value})
