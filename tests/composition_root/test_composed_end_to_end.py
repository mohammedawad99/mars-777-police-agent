"""The composed graph, driven for real: two agents, two sessions, one turn.

The production composition starts nothing, so this test does the starting - it
runs the servers it was handed, enters the clients it was handed, and binds the
runtimes. Everything it drives is the object graph `compose_agent` returned.
"""

import asyncio
from collections.abc import Iterator

import audit_builders
import composed_builders as build
import pytest
import turn_builders
from live_server import LiveServer
from peer_ops import step0_exchange
from r16_builders import GROUP_A, GROUP_B

from mars777_police.app.protocol_errors import AuthFailureError, StaleMessageError
from mars777_police.app.sealed_record_values import ActorRole, Intent
from mars777_police.app.turn_cursor import TurnCursor
from mars777_police.transport.client import PeerClient
from mars777_police.transport.peer_transport import FastMcpPeerTransport

CURSOR = TurnCursor(build.FIRST_SUB_GAME, 1)


@pytest.fixture
def pair() -> Iterator[tuple[object, object]]:
    """Two composed agents, each behind the real server its composition built."""
    a, b = build.both("http://127.0.0.1:1/mcp", "http://127.0.0.1:2/mcp")
    with (
        LiveServer(a.inbound_operations, "composed-a") as server_a,
        LiveServer(b.inbound_operations, "composed-b") as server_b,
    ):
        yield (a, server_a.url), (b, server_b.url)


def bind_sub_game(composition: object, role: ActorRole) -> None:
    """Give the composition a live sub-game and turn, as R6 later will."""
    composition.runtime_context.bind_sub_game(build.evidence_for(role), audit_builders.runtime())
    composition.runtime_context.bind_turn(turn_builders.runtime(role))


async def held_runner(composition: object, url: str) -> tuple[object, object]:
    """Enter a real session and return the runner bound to it."""
    client = await PeerClient(url, timeout=20.0).__aenter__()
    transport = FastMcpPeerTransport(client)
    import dataclasses

    return dataclasses.replace(composition.peer_runner, transport=transport), client


def test_the_composed_graph_completes_a_real_callback_turn(pair: tuple) -> None:
    """Commitment → Acknowledgement → Reveal, across the composed agents."""
    (a, url_a), (b, url_b) = pair
    bind_sub_game(a, ActorRole.POLICE)
    bind_sub_game(b, ActorRole.THIEF)

    async def run() -> bool:
        runner_a, _ = await held_runner(a, url_b)
        runner_b, _ = await held_runner(b, url_a)
        await runner_a.send_step0(a.identity.declaration)
        await runner_b.send_step0(b.identity.declaration)
        prepared = await runner_a.open_turn(
            state=build.sealed(ActorRole.POLICE),
            action=turn_builders.legal_reveal().action,
            intent=Intent.TRUTH,
            hint="heading north",
            cursor=CURSOR,
        )
        assert b.runtime_context.current_turn().peer_commitment is not None
        await runner_b.acknowledge_peer_turn()
        assert a.runtime_context.current_turn().local_acknowledged
        return await runner_a.reveal_turn(prepared)

    assert asyncio.run(run()).accepted is True


def test_a_fresh_session_cannot_continue_the_composed_conversation(pair: tuple) -> None:
    (a, _), (_b, url_b) = pair
    bind_sub_game(a, ActorRole.POLICE)

    async def run() -> None:
        runner, client = await held_runner(a, url_b)
        await runner.send_step0(a.identity.declaration)
        await client.__aexit__(None, None, None)
        async with PeerClient(url_b, timeout=20.0) as fresh:
            with pytest.raises(AuthFailureError):
                await FastMcpPeerTransport(fresh).send_commitment(turn_builders.commitment())

    asyncio.run(run())


def test_gameplay_works_while_no_result_owner_exists(pair: tuple) -> None:
    """The whole point of late binding: the series can be played first."""
    (a, _), (b, url_b) = pair
    bind_sub_game(a, ActorRole.POLICE)
    bind_sub_game(b, ActorRole.THIEF)
    assert a.runtime_context.result is None and b.runtime_context.result is None

    async def run() -> None:
        runner, _ = await held_runner(a, url_b)
        await runner.send_step0(a.identity.declaration)
        await runner.open_turn(
            state=build.sealed(ActorRole.POLICE),
            action=turn_builders.legal_reveal().action,
            intent=Intent.TRUTH,
            hint="heading north",
            cursor=CURSOR,
        )
        with pytest.raises(StaleMessageError, match="not available yet"):
            await runner.open_result_agreement()

    asyncio.run(run())
    assert b.runtime_context.current_turn().peer_commitment is not None
    assert GROUP_A != GROUP_B and step0_exchange() is not None
