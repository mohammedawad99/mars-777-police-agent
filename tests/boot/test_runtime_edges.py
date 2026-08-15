"""The lifecycle edges: refusals, the context manager, and safe cleanup.

Split from `test_agent_runtime` when that file reached its limit; these are the
paths a caller reaches by using the runtime out of order or half-way.
"""

import asyncio
import socket

import boot_builders as build
import pytest

from mars777_police.agent_runtime import RuntimeState, release
from mars777_police.app.protocol_errors import LocalDefectError, StaleMessageError


def test_connecting_before_serving_is_refused() -> None:
    runtime = build.runtime_for(build.agent())
    with pytest.raises(LocalDefectError, match="cannot connect while NEW"):
        asyncio.run(runtime.connect())


def test_waiting_before_serving_is_refused() -> None:
    runtime = build.runtime_for(build.agent())
    with pytest.raises(LocalDefectError, match="not serving"):
        asyncio.run(runtime.wait_closed())


def test_the_async_context_starts_and_stops_the_whole_agent() -> None:
    """`start` needs the opponent listening, so a second runtime provides it."""
    port_a, port_b = build.pair_urls()
    url_b = f"http://{build.HOST}:{port_b}/mcp"
    opponent = build.runtime_for(
        build.agent(*build.other(), f"http://{build.HOST}:{port_a}/mcp"), port_b
    )
    composition = build.agent(opponent=url_b)
    runtime = build.runtime_for(composition, port_a)

    async def run() -> None:
        await opponent.serve()
        try:
            async with runtime as live:
                assert live is runtime
                assert live.state is RuntimeState.RUNNING
                assert composition.peer_client._session is not None
        finally:
            await opponent.stop()

    asyncio.run(run())
    assert runtime.state is RuntimeState.CLOSED
    assert composition.peer_client._session is None


def test_releasing_nothing_is_safe() -> None:
    """Cleanup is callable from every point a startup can fail at."""

    asyncio.run(release(None, None))


def test_releasing_a_socket_without_a_server_closes_it() -> None:

    listener = socket.socket()
    listener.bind((build.HOST, 0))
    asyncio.run(release(None, listener))
    with pytest.raises(OSError):
        listener.getsockname()


def test_starting_twice_is_refused() -> None:
    runtime = build.runtime_for(build.agent())

    async def run() -> None:
        await runtime.serve()
        try:
            with pytest.raises(LocalDefectError, match="cannot serve while SERVING"):
                await runtime.serve()
        finally:
            await runtime.stop()

    asyncio.run(run())
    with pytest.raises(LocalDefectError, match="cannot serve while CLOSED"):
        asyncio.run(runtime.start())


def test_stopping_is_idempotent_and_safe_before_start() -> None:
    runtime = build.runtime_for(build.agent())
    asyncio.run(runtime.stop())
    assert runtime.state is RuntimeState.NEW

    async def run() -> None:
        await runtime.serve()
        await runtime.stop()
        await runtime.stop()

    asyncio.run(run())
    assert runtime.state is RuntimeState.CLOSED


def test_the_address_is_unavailable_before_the_ingress_is_bound() -> None:
    with pytest.raises(LocalDefectError, match="not serving"):
        _ = build.runtime_for(build.agent()).address


def test_cancelling_the_waiter_still_releases_everything() -> None:
    composition = build.agent()
    runtime = build.runtime_for(composition)

    async def run() -> None:
        await runtime.serve()
        try:
            waiter = asyncio.create_task(asyncio.Event().wait())
            waiter.cancel()
            with pytest.raises(asyncio.CancelledError):
                await waiter
        finally:
            await runtime.stop()

    asyncio.run(run())
    assert runtime.state is RuntimeState.CLOSED
    assert composition.peer_client._session is None
    released = socket.socket()
    released.bind((build.HOST, runtime.port))
    released.close()


def test_boot_binds_no_game_runtime_and_no_result() -> None:
    composition = build.agent()

    runtime = build.runtime_for(composition)

    async def run() -> None:
        await runtime.serve()
        try:
            for accessor in ("current_turn", "current_evidence", "current_audit"):
                with pytest.raises(StaleMessageError):
                    getattr(composition.runtime_context, accessor)()
            with pytest.raises(StaleMessageError, match="not available yet"):
                composition.runtime_context.current_result()
        finally:
            await runtime.stop()

    asyncio.run(run())


def test_waiting_on_a_served_ingress_returns_when_it_ends() -> None:
    """`wait_closed` parks on the server task and returns once it is over.

    Boot no longer parks here - it plays a series and stops - but the operation
    is still the lifecycle owner's way to hand a process to the server, so the
    path that actually awaits is exercised rather than left to a caller.
    """
    runtime = build.runtime_for(build.agent())

    async def serve_then_end() -> None:
        await runtime.serve()
        try:
            task = runtime.server_task
            assert task is not None
            task.cancel()
            await runtime.wait_closed()
        finally:
            await runtime.stop()

    asyncio.run(serve_then_end())
