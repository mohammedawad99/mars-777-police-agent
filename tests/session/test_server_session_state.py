"""The server's own session-state seam, exercised in process.

The subprocess proofs show the whole path works over real HTTP; these run the
same production server in-memory so the read/write helpers themselves are
covered, including the branch where the store holds nothing yet.
"""

import asyncio

import audit_builders
import pytest
import session_builders as build
import session_calls
import turn_builders
from fastmcp import Client
from session_peer import turn_sequence

from mars777_police.transport.peer_operations import InboundPeerOperations
from mars777_police.transport.server import AUTH_STATE_KEY, build_server


def server_and_pregame() -> tuple[object, object]:
    """The production server, and the series-scoped pregame runtime behind it."""
    pregame = build.pregame()
    pregame.adopt_config(build.agreed())
    audit = audit_builders.runtime()
    operations = InboundPeerOperations(pregame, turn_sequence(), lambda: audit, build.exchange())
    return build_server(operations, name="r3r-inmemory"), pregame


def server() -> object:
    """Just the server, for the tests that do not reach behind it."""
    return server_and_pregame()[0]


async def send(client: Client, tool: str, kind: str, payload: object) -> object:
    """One call in the frozen envelope shape."""
    result = await client.call_tool(tool, {"request": {"kind": kind, "payload": payload}})
    return result.data


def test_every_kind_succeeds_in_process_on_one_session() -> None:
    """Same nine operations, same adapter, no subprocess and no HTTP."""

    async def run() -> list[object]:
        async with Client(server()) as client:
            return [await send(client, t, k, p) for t, k, p in session_calls.payloads()]

    results = asyncio.run(run())
    assert results[5] is True
    assert isinstance(results[8], str) and len(results[8]) == 64


def test_an_unauthenticated_call_reads_an_empty_store_and_refuses() -> None:
    """The `None` branch of the state read: nothing bound, nothing granted."""
    from fastmcp.exceptions import ToolError

    async def run() -> None:
        async with Client(server()) as client:
            await send(
                client,
                "receive_turn",
                "commitment",
                session_calls.payloads()[3][2],
            )

    with pytest.raises(ToolError, match="E-AUTH-FAILURE"):
        asyncio.run(run())


def test_the_state_key_is_the_single_documented_one() -> None:
    assert AUTH_STATE_KEY == "mars777.authenticated_peer"


def test_a_failed_step0_writes_nothing_back() -> None:
    """The write-back is after the operation, so a refusal leaves the store empty."""
    from fastmcp.exceptions import ToolError

    from mars777_police.transport.codec_declaration import encode_step0

    async def run() -> None:
        async with Client(server()) as client:
            with pytest.raises(ToolError, match="E-AUTH-FAILURE"):
                await send(client, "negotiate", "step0", encode_step0(session_calls.forged_step0()))
            with pytest.raises(ToolError, match="E-AUTH-FAILURE"):
                await send(
                    client,
                    "receive_turn",
                    "commitment",
                    session_calls.payloads()[3][2],
                )

    asyncio.run(run())
    assert turn_builders is not None


def test_the_authenticated_session_survives_a_config_round_change() -> None:
    """A new sub-game is not a new peer: Step-0 is not repeated for `g02`."""
    live, pregame = server_and_pregame()

    async def run() -> str | None:
        async with Client(live) as client:
            await send(client, *session_calls.payloads()[0][:2], session_calls.payloads()[0][2])
            pregame.open_round(*build.round_of(2))
            assert pregame.peer is not None
            await send(client, "receive_turn", "commitment", session_calls.payloads()[3][2])
            return pregame.peer

    assert asyncio.run(run()) == pregame_peer()


def pregame_peer() -> str:
    """The identity Step-0 verifies in these fixtures."""
    from r16_builders import GROUP_B

    return str(GROUP_B)
