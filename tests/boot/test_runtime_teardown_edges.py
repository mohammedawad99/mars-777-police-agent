"""Which socket-level teardown failures end a run, and which are its ending.

When a run is over, Windows' proactor aborts the outstanding operations of the
session being closed and reports `WinError 995`. The series has already finished
by then, so letting that turn a completed run into a failed process would be a
lie about what happened. It is recognised by the verified error number and by
nothing else - no platform test, no error class, no message.
"""

import asyncio
import socket
from collections.abc import Callable

import boot_builders as build
import pytest

from mars777_police.agent_runtime import RuntimeState

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
