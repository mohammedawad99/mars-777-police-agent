"""The other shape of the same ending: the request that never gets its answer.

Behind the socket abort is a second one - the in-flight Streamable-HTTP POST of
the session being disconnected, whose peer has already gone, so the read times
out. Same rule as its sibling: benign only where the run had already finished,
and every other transport failure still fails.
"""

import asyncio
import socket

import httpx
import pytest
from test_runtime_teardown_edges import _holding_a_session

from mars777_police.agent_runtime import RuntimeState

"""`WinError 995`: the I/O operation was aborted by a thread or process exit.

What Windows' IOCP proactor raises while the held peer session is closed at the
end of a run. The series is already over - artifacts written, result agreed -
so it is the sound of a session ending, not of one failing. Every other
teardown failure still means what it always meant.
"""


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
