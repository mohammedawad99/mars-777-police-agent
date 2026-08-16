"""Two agents booted through the production lifecycle, then made to play.

Both ports are chosen before either agent is composed, so each knows the other's
ingress. Both servers come up first, then both clients connect - the ordering the
audited `PeerClient.__aenter__` actually requires, with no sleep anywhere.
"""

import asyncio
import dataclasses
import socket
from collections.abc import AsyncIterator, Iterator
from contextlib import asynccontextmanager

import audit_builders
import boot_builders as build
import composed_builders as compose
import pytest
import turn_builders
from r16_builders import GROUP_A, GROUP_B

from mars777_police.agent_runtime import AgentRuntime, RuntimeState
from mars777_police.app.peer_supervision import PeerDeadline, TimeoutPolicy
from mars777_police.app.protocol_errors import AuthFailureError
from mars777_police.app.sealed_record_values import ActorRole, Intent
from mars777_police.app.turn_cursor import TurnCursor
from mars777_police.transport.client import PeerClient
from mars777_police.transport.peer_transport import FastMcpPeerTransport

CURSOR = TurnCursor(compose.FIRST_SUB_GAME, 1)
TIMEOUT = 20.0


@pytest.fixture
def agents() -> Iterator[tuple[AgentRuntime, AgentRuntime]]:
    """Two composed agents, each pointed at the other's future ingress."""
    port_a, port_b = build.pair_urls()
    url_a = f"http://{build.HOST}:{port_a}/mcp"
    url_b = f"http://{build.HOST}:{port_b}/mcp"
    a = build.runtime_for(compose.compose(GROUP_A, "group_a", ActorRole.POLICE, url_b), port_a)
    b = build.runtime_for(compose.compose(GROUP_B, "group_b", ActorRole.THIEF, url_a), port_b)
    yield a, b


@asynccontextmanager
async def booted(a: AgentRuntime, b: AgentRuntime) -> AsyncIterator[None]:
    """Servers first, then clients - the order the client API demands.

    Both are stopped inside the same event loop that entered them; exiting an
    async client from a different loop is how resources get left behind.
    """
    await a.serve()
    await b.serve()
    await a.connect()
    await b.connect()
    try:
        yield
    finally:
        await a.stop()
        await b.stop()


def bind_game(runtime: AgentRuntime, role: ActorRole) -> None:
    """Give an agent a live sub-game, as the future orchestrator will."""
    context = runtime.composition.runtime_context
    context.bind_sub_game(compose.evidence_for(role), audit_builders.runtime())
    context.bind_turn(turn_builders.runtime(role))


def test_both_agents_boot_and_hold_persistent_sessions(agents: tuple) -> None:
    a, b = agents

    async def run() -> None:
        async with booted(a, b):
            assert a.state is b.state is RuntimeState.RUNNING
            assert a.composition.peer_client._session is not None
            assert b.composition.peer_client._session is not None
            assert a.composition.pregame.peer is None and b.composition.pregame.peer is None

    asyncio.run(run())
    assert a.state is b.state is RuntimeState.CLOSED


def test_a_full_callback_turn_runs_through_the_booted_agents(agents: tuple) -> None:
    """R4's topology, unchanged, over lifecycles R6 owns."""
    a, b = agents
    bind_game(a, ActorRole.POLICE)
    bind_game(b, ActorRole.THIEF)

    async def run() -> bool:
        async with booted(a, b):
            runner_a, runner_b = a.composition.peer_runner, b.composition.peer_runner
            await runner_a.send_step0(a.composition.identity.declaration)
            await runner_b.send_step0(b.composition.identity.declaration)
            prepared = await runner_a.open_turn(
                state=compose.sealed(ActorRole.POLICE),
                action=turn_builders.legal_reveal().action,
                intent=Intent.TRUTH,
                hint="heading north",
                cursor=CURSOR,
            )
            await runner_b.acknowledge_peer_turn()
            return await runner_a.reveal_turn(prepared)

    assert asyncio.run(run()).accepted is True


def test_a_fresh_session_is_still_refused_after_boot(agents: tuple) -> None:
    """R6 changes lifecycle, not session security."""
    a, b = agents
    bind_game(a, ActorRole.POLICE)

    async def run() -> None:
        async with booted(a, b):
            await a.composition.peer_runner.send_step0(a.composition.identity.declaration)
            async with PeerClient(b.address, PeerDeadline(TimeoutPolicy(TIMEOUT))) as fresh:
                with pytest.raises(AuthFailureError):
                    await FastMcpPeerTransport(fresh).send_commitment(turn_builders.commitment())

    asyncio.run(run())


def test_shutdown_after_real_traffic_releases_everything(agents: tuple) -> None:
    a, b = agents
    bind_game(a, ActorRole.POLICE)
    ports = (a.port, b.port)

    async def run() -> None:
        async with booted(a, b):
            await a.composition.peer_runner.send_step0(a.composition.identity.declaration)

    asyncio.run(run())
    assert a.state is b.state is RuntimeState.CLOSED
    assert a.composition.peer_client._session is None
    assert b.composition.peer_client._session is None
    for port in ports:
        released = socket.socket()
        released.bind((build.HOST, port))
        released.close()


def test_the_runtime_reuses_the_exact_composed_objects(agents: tuple) -> None:
    """No lifecycle reconstruction: BOOT drives what composition built."""
    a, _ = agents
    composition = a.composition
    assert a.composition is composition
    assert composition.peer_runner.transport is composition.peer_transport
    assert dataclasses.replace(composition.identity) == composition.identity
