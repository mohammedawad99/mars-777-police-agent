"""The lifecycle edges: refusals, the context manager, and safe cleanup.

Split from `test_agent_runtime` when that file reached its limit; these are the
paths a caller reaches by using the runtime out of order or half-way.
"""

import asyncio
import socket
from collections.abc import Callable

import boot_builders as build
import httpx
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


ABORTED = 995
"""`WinError 995`: the I/O operation was aborted by a thread or process exit.

What Windows' IOCP proactor raises while the held peer session is closed at the
end of a run. The series is already over - artifacts written, result agreed -
so it is the sound of a session ending, not of one failing. Every other
teardown failure still means what it always meant.
"""


def aborted_session(winerror: int | None = ABORTED) -> Callable[..., object]:
    """A peer-session close that fails the way Windows fails at the very end."""

    async def close(*_: object) -> None:
        failure = OSError(winerror or 5, "the I/O operation has been aborted")
        if winerror is not None:
            failure.winerror = winerror  # type: ignore[attr-defined]
        raise failure

    return close


def broken_session() -> Callable[..., object]:
    """A teardown failure that is not an `OSError` at all."""

    async def close(*_ignored: object) -> None:
        raise RuntimeError("the session could not be closed")

    return close


def _holding_a_session(monkeypatch: pytest.MonkeyPatch, close: object) -> object:
    """A runtime that has served and holds an open outbound session."""
    composition = build.agent()
    runtime = build.runtime_for(composition)
    monkeypatch.setattr(type(composition.peer_client), "__aexit__", close)
    return runtime


def test_a_windows_session_abort_does_not_fail_a_finished_run(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The exact terminal condition: stop returns, and the ingress is released."""
    runtime = _holding_a_session(monkeypatch, aborted_session())

    async def finish() -> socket.socket:
        await runtime.serve()  # type: ignore[attr-defined]
        runtime.state = RuntimeState.RUNNING  # type: ignore[attr-defined]
        listener, task = runtime.listener, runtime.server_task  # type: ignore[attr-defined]
        assert listener is not None and task is not None
        await runtime.stop()  # type: ignore[attr-defined]
        assert task.done()
        return listener

    listener = asyncio.run(finish())
    assert runtime.state is RuntimeState.CLOSED  # type: ignore[attr-defined]
    assert runtime.listener is None and runtime.server_task is None  # type: ignore[attr-defined]
    assert listener.fileno() == -1


def test_a_different_oserror_still_fails_after_the_ingress_is_released(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`except OSError: pass` would have swallowed this one; the rule is narrower."""
    runtime = _holding_a_session(monkeypatch, aborted_session(winerror=64))

    async def finish() -> socket.socket:
        await runtime.serve()  # type: ignore[attr-defined]
        runtime.state = RuntimeState.RUNNING  # type: ignore[attr-defined]
        listener = runtime.listener  # type: ignore[attr-defined]
        assert listener is not None
        with pytest.raises(OSError) as raised:
            await runtime.stop()  # type: ignore[attr-defined]
        assert getattr(raised.value, "winerror", None) == 64
        return listener

    listener = asyncio.run(finish())
    assert listener.fileno() == -1


def test_an_oserror_without_a_winerror_is_never_benign(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """No `winerror` means no ruling applies - on Linux this is every `OSError`."""
    runtime = _holding_a_session(monkeypatch, aborted_session(winerror=None))

    async def finish() -> None:
        await runtime.serve()  # type: ignore[attr-defined]
        runtime.state = RuntimeState.RUNNING  # type: ignore[attr-defined]
        with pytest.raises(OSError):
            await runtime.stop()  # type: ignore[attr-defined]

    asyncio.run(finish())


def test_a_non_oserror_teardown_failure_still_propagates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Nothing broad is swallowed: only the one approved Windows condition."""
    runtime = _holding_a_session(monkeypatch, broken_session())

    async def finish() -> socket.socket:
        await runtime.serve()  # type: ignore[attr-defined]
        runtime.state = RuntimeState.RUNNING  # type: ignore[attr-defined]
        listener = runtime.listener  # type: ignore[attr-defined]
        assert listener is not None
        with pytest.raises(RuntimeError, match="could not be closed"):
            await runtime.stop()  # type: ignore[attr-defined]
        return listener

    listener = asyncio.run(finish())
    assert listener.fileno() == -1


class CountedClose:
    """A peer-session close that fails, and remembers how often it was asked.

    Teardown is attempted exactly once whatever it raises: a benign ending is
    not a reason to go back and try closing the session again.
    """

    def __init__(self, failure: BaseException) -> None:
        self.failure, self.attempts = failure, 0

    async def __call__(self, *_ignored: object) -> None:
        self.attempts += 1
        raise self.failure


def test_a_terminal_read_timeout_does_not_fail_a_finished_run(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The second observed terminal condition, at the same session-close seam.

    Windows exact-SHA CI played the whole series and then exited non-zero: the
    in-flight Streamable-HTTP POST of the session being disconnected never got
    its answer, because the peer it was talking to had already gone. That read
    timing out is the shape of a finished conversation, not of a broken one.
    """
    close = CountedClose(httpx.ReadTimeout("the read timed out"))
    runtime = _holding_a_session(monkeypatch, close)

    async def finish() -> socket.socket:
        await runtime.serve()  # type: ignore[attr-defined]
        runtime.state = RuntimeState.RUNNING  # type: ignore[attr-defined]
        listener, task = runtime.listener, runtime.server_task  # type: ignore[attr-defined]
        assert listener is not None and task is not None
        await runtime.stop()  # type: ignore[attr-defined]
        assert task.done()
        return listener

    listener = asyncio.run(finish())
    assert close.attempts == 1
    assert runtime.state is RuntimeState.CLOSED  # type: ignore[attr-defined]
    assert runtime.listener is None and runtime.server_task is None  # type: ignore[attr-defined]
    assert listener.fileno() == -1


@pytest.mark.parametrize(
    "failure",
    [
        httpx.ConnectTimeout("the connection timed out"),
        httpx.ConnectError("the connection was refused"),
    ],
    ids=["connect-timeout", "connect-error"],
)
def test_another_httpx_failure_still_fails_after_the_ingress_is_released(
    monkeypatch: pytest.MonkeyPatch, failure: httpx.HTTPError
) -> None:
    """The rule is one exact type, not a family.

    `ConnectTimeout` is the sibling `TimeoutException` and `ConnectError` the
    wider `TransportError`, so between them they refuse every broader spelling
    this could have been written as. Neither one can be the sound of a session
    ending: a run that reached teardown had already connected.
    """
    runtime = _holding_a_session(monkeypatch, CountedClose(failure))

    async def finish() -> socket.socket:
        await runtime.serve()  # type: ignore[attr-defined]
        runtime.state = RuntimeState.RUNNING  # type: ignore[attr-defined]
        listener = runtime.listener  # type: ignore[attr-defined]
        assert listener is not None
        with pytest.raises(type(failure)) as raised:
            await runtime.stop()  # type: ignore[attr-defined]
        assert raised.value is failure
        return listener

    listener = asyncio.run(finish())
    assert listener.fileno() == -1
