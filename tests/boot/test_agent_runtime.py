"""Starting, stopping, failing to start, and being cancelled."""

import asyncio
import socket

import boot_builders as build
import pytest

from mars777_police.agent_runtime import AgentRuntime, RuntimeState
from mars777_police.app.protocol_errors import LocalDefectError


def assert_started_nothing(runtime: AgentRuntime) -> None:
    """A failed startup keeps nothing: not the state, the task, or the port."""
    assert runtime.state is RuntimeState.NEW
    assert runtime.server_task is None and runtime.listener is None
    assert runtime.composition.peer_client._session is None
    freed = socket.socket()
    freed.bind((build.HOST, runtime.port))
    freed.close()


def test_a_new_runtime_has_started_nothing() -> None:
    runtime = build.runtime_for(build.agent())
    assert runtime.state is RuntimeState.NEW
    assert runtime.server_task is None and runtime.listener is None
    assert runtime.composition.peer_client._session is None


def test_serving_makes_the_ingress_reachable_immediately() -> None:
    """Readiness is the bind: a connection right after `serve` is accepted."""
    composition = build.agent()
    runtime = build.runtime_for(composition)

    async def run() -> None:
        await runtime.serve()
        assert runtime.state is RuntimeState.SERVING
        assert runtime.address.startswith("http://127.0.0.1:")
        reader, writer = await asyncio.open_connection(build.HOST, runtime.port)
        assert reader is not None
        writer.close()
        await writer.wait_closed()
        await runtime.stop()

    asyncio.run(run())
    assert runtime.state is RuntimeState.CLOSED
    assert composition.peer_client._session is None
    assert runtime.server_task is None and runtime.listener is None


def test_boot_sends_nothing_to_the_peer() -> None:
    """Entering the client is transport lifecycle; it is not gameplay."""
    composition = build.agent()
    runtime = build.runtime_for(composition)

    async def run() -> None:
        await runtime.serve()
        try:
            assert composition.pregame.peer is None
            assert composition.pregame.opening and composition.pregame.seen == frozenset()
            assert composition.runtime_context.turn is None
        finally:
            await runtime.stop()

    asyncio.run(run())


def test_a_port_already_in_use_fails_before_anything_starts() -> None:
    """Deterministic: the bind is ours, so the conflict raises in our frame."""
    holder = socket.socket()
    holder.bind((build.HOST, 0))
    holder.listen(1)
    composition = build.agent()
    runtime = AgentRuntime(composition, build.HOST, holder.getsockname()[1])
    try:
        with pytest.raises(OSError):
            asyncio.run(runtime.start())
    finally:
        holder.close()
    assert runtime.state is RuntimeState.NEW
    assert composition.peer_client._session is None
    assert runtime.server_task is None and runtime.listener is None


def test_a_route_the_server_refuses_fails_startup_rather_than_serving() -> None:
    """The real vector: a path FastMCP rejects kills the task in its first step.

    The bind still succeeds, so only the startup checkpoint can catch this - and
    `serve` itself must raise the server's own error, not report `SERVING` and
    leave the failure for whoever happens to await the task later.
    """
    runtime = AgentRuntime(build.agent(), build.HOST, build.free_port(), path="mcp")
    with pytest.raises(AssertionError, match="must start with"):
        asyncio.run(runtime.serve())
    assert_started_nothing(runtime)


def test_an_immediately_failing_server_task_raises_its_own_cause() -> None:
    composition = build.agent()
    runtime = build.runtime_for(composition)

    async def collapse(**_kwargs: object) -> None:
        raise RuntimeError("the server died in its first step")

    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(composition.server, "run_http_async", collapse)
        with pytest.raises(RuntimeError, match="first step"):
            asyncio.run(runtime.serve())
    assert_started_nothing(runtime)


def test_a_server_that_ends_without_failing_is_still_a_failed_startup() -> None:
    """Nothing raised, but nothing is serving either - so `SERVING` would lie."""
    composition = build.agent()
    runtime = build.runtime_for(composition)

    async def ended(**_kwargs: object) -> None:
        return None

    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(composition.server, "run_http_async", ended)
        with pytest.raises(LocalDefectError, match="stopped before it served"):
            asyncio.run(runtime.serve())
    assert_started_nothing(runtime)


def test_a_failing_client_entry_stops_the_server_it_already_started() -> None:
    """No half-booted runtime: the ingress is gone before the error escapes."""
    composition = build.agent()
    runtime = build.runtime_for(composition)
    port = runtime.port

    async def refuse(_self: object) -> None:
        raise RuntimeError("the peer client refused to enter")

    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(type(composition.peer_client), "__aenter__", refuse, raising=True)
        with pytest.raises(RuntimeError, match="refused to enter"):
            asyncio.run(runtime.start())
    assert runtime.state is RuntimeState.CLOSED
    assert runtime.server_task is None and runtime.listener is None
    free = socket.socket()
    free.bind((build.HOST, port))
    free.close()
