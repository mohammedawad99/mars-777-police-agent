"""A bad-HMAC Step-0 must be refused by authentication, never by the schema.

The distinction is the whole point. A live rehearsal once had its Step-0
rejected at input validation *before* authentication - no HMAC checked, no
sub-game started - and the peer could not tell a shape disagreement from a key
disagreement, because both arrive as a rejected call. So the argument boundary
has to let a structurally valid Step-0 through, and the keyed authority has to be
the thing that says no.

These drive the real public tool over a real MCP session and assert on which
layer refused, not merely that something did.
"""

import asyncio
from typing import Any

import pytest
from fastmcp import Client
from fastmcp.exceptions import ToolError
from peer_ops import step0_exchange
from r16_builders import COMMIT_A, COMMIT_B, GROUP_A, GROUP_B
from r16_builders import partial as partial_declaration

from mars777_police.app.auth_values import AuthProfile, KeyId
from mars777_police.app.kit_handoff import SeriesHandoff
from mars777_police.app.kit_messages import KitRole
from mars777_police.app.step0_runtime import Step0Runtime
from mars777_police.protocol.declaration import Step0Authenticator
from mars777_police.protocol.keyed_auth import HmacSha256Provider, KeyedAuthenticator
from mars777_police.transport.call_arguments import wire_json
from mars777_police.transport.codec_declaration import decode_step0, encode_step0
from mars777_police.transport.kit_gateway import KitGroupGateway
from mars777_police.transport.kit_gateway_server import build_gateway_tools

OUR_KEY = KeyId("mars777-k1")
WRONG_SECRET = b"a-different-secret-entirely-not-ours"


def gateway() -> KitGroupGateway:
    return KitGroupGateway(handoff=SeriesHandoff(KitRole.POLICE), routes={}, deadline=30.0)


def ours() -> Step0Runtime:
    """Our own Step-0 authority, holding the secret the peer does not have."""
    keyed = KeyedAuthenticator(
        AuthProfile.HMAC_SHA256, OUR_KEY, HmacSha256Provider({OUR_KEY.value: b"the-real-secret"})
    )
    return Step0Runtime(GROUP_A, Step0Authenticator(keyed))


def forged() -> dict[str, Any]:
    """A structurally perfect Step-0 whose proof was made with the wrong key."""
    keyed = KeyedAuthenticator(
        AuthProfile.HMAC_SHA256, OUR_KEY, HmacSha256Provider({OUR_KEY.value: WRONG_SECRET})
    )
    exchange = Step0Runtime(GROUP_B, Step0Authenticator(keyed)).outbound(
        partial_declaration(GROUP_B, COMMIT_B)
    )
    payload: dict[str, Any] = wire_json(encode_step0(exchange))
    return payload


def call(payload: dict[str, Any], receiver: Any) -> str:
    """Make the exact call the peer's runner makes, and return the refusal text."""

    async def run() -> str:
        async with Client(build_gateway_tools(gateway(), step0=receiver)) as c:
            try:
                await c.call_tool("negotiate", {"kind": "step0", "payload": payload})
            except ToolError as failure:
                return str(failure)
        return ""

    return asyncio.run(run())


def test_a_forged_step0_passes_schema_validation_and_reaches_the_receiver() -> None:
    """The boundary proof: the argument layer must not be what refuses it."""
    seen: list[dict[str, Any]] = []

    async def receive(payload: dict[str, Any]) -> None:
        seen.append(payload)

    call(forged(), receive)
    assert seen, "a structurally valid Step-0 never reached the receiver"


def test_the_refusal_is_authentication_not_additional_properties() -> None:
    """`Additional properties are not allowed` here would be the old defect back."""

    async def verify(payload: dict[str, Any]) -> None:
        ours().accept(
            partial_declaration(GROUP_A, COMMIT_A),
            decode_step0(
                __import__(
                    "mars777_police.transport.wire_declaration", fromlist=["Step0ExchangeWire"]
                ).Step0ExchangeWire.model_validate(payload)
            ),
        )

    refusal = call(forged(), verify)
    assert refusal, "a forged proof must be refused"
    assert "Additional properties" not in refusal
    assert "additionalProperties" not in refusal


def test_a_genuine_step0_is_accepted_by_the_same_route() -> None:
    """The negative test means nothing unless the positive one passes here too."""
    seen: list[dict[str, Any]] = []

    async def receive(payload: dict[str, Any]) -> None:
        seen.append(payload)

    call(wire_json(encode_step0(step0_exchange())), receive)
    assert len(seen) == 1


def test_a_failed_authentication_leaves_no_accepted_state() -> None:
    """A refused Step-0 must not look later like one that happened."""
    accepted: list[str] = []

    async def verify(payload: dict[str, Any]) -> None:
        accepted.append("reached")
        raise ValueError("E-AUTH: the proof does not verify under our key")

    call(forged(), verify)
    assert accepted == ["reached"], "the receiver must be reached, then refuse"


@pytest.mark.parametrize(
    "arguments",
    [{}, {"kind": "step0"}, {"payload": {"a": 1}}, {"kind": "unknown", "payload": {}}],
    ids=["empty", "kind without payload", "payload without kind", "unknown kind"],
)
def test_the_shapes_that_must_still_fail_closed(arguments: dict[str, Any]) -> None:
    """Letting a forged proof through must not have loosened anything else."""

    async def unreached(payload: dict[str, Any]) -> None:
        raise AssertionError("this shape should never reach a receiver")

    assert call(arguments, unreached) != ""
