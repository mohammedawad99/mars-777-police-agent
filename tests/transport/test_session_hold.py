"""Which endings get a second attempt, and which are terminal.

The recovery in `session_hold` is only as safe as its discrimination: a peer
that *states* it has no such session has proven it never dispatched the body,
and everything else may have been dispatched with the outcome unknown. These
tests pin that line, because widening it would turn `E-TRANSPORT` from a refusal
to replay a commitment into a silent double-send.
"""

import asyncio

import pytest
from mcp.shared.exceptions import McpError
from mcp.types import ErrorData
from session_doubles import OpenedSession, session_gone

from mars777_police.app.protocol_errors import LocalDefectError
from mars777_police.transport.session_hold import (
    SESSION_NOT_FOUND_CODE,
    SESSION_NOT_FOUND_TEXT,
    HeldSession,
    session_not_found,
)


def test_the_peer_stating_it_has_no_such_session_is_recognised() -> None:
    assert session_not_found(session_gone())


def test_the_recognised_answer_is_the_one_the_client_actually_raises() -> None:
    """Pinned against the library: both halves, so a drift is loud, not silent."""
    assert SESSION_NOT_FOUND_CODE == 32600
    assert SESSION_NOT_FOUND_TEXT == "session terminated"


@pytest.mark.parametrize(
    "failure",
    [
        McpError(ErrorData(code=SESSION_NOT_FOUND_CODE, message="Invalid request")),
        McpError(ErrorData(code=-32603, message="Session terminated")),
        RuntimeError("Session terminated"),
        TimeoutError(),
    ],
    ids=["right code wrong text", "right text wrong code", "not an McpError", "a timeout"],
)
def test_every_other_ending_is_left_alone(failure: BaseException) -> None:
    """The narrowness is the safety: anything that may have arrived stays terminal."""
    assert not session_not_found(failure)


def test_calling_without_a_held_session_is_a_local_defect() -> None:
    hold = HeldSession(OpenedSession)

    async def drive() -> None:
        await hold.run(_unreached)

    with pytest.raises(LocalDefectError, match="no outbound session is held"):
        asyncio.run(drive())


async def _unreached(_: object) -> object:
    raise AssertionError("a call was made with no session held")


def test_a_request_that_may_have_been_dispatched_is_never_re_issued() -> None:
    """The rule `E-TRANSPORT` exists for, stated as an executable fact."""
    calls: list[int] = []

    async def failing(_: object) -> object:
        calls.append(1)
        raise McpError(ErrorData(code=-32603, message="Internal error"))

    hold = HeldSession(OpenedSession)

    async def drive() -> None:
        await hold.open()
        await hold.run(failing)

    with pytest.raises(McpError):
        asyncio.run(drive())
    assert calls == [1]
    assert hold.reestablished == 0


def test_a_disowned_session_is_replaced_and_the_request_issued_once_more() -> None:
    """One fresh session, one second attempt, and the retired id never reused."""
    calls: list[str] = []
    opened: list[OpenedSession] = []

    async def once(session: object) -> str:
        calls.append(session.get_session_id())  # type: ignore[attr-defined]
        if len(calls) == 1:
            raise session_gone()
        return "delivered"

    def opener() -> OpenedSession:
        opened.append(OpenedSession(f"session-{len(opened)}"))
        return opened[-1]

    async def drive() -> str:
        hold = HeldSession(opener)
        await hold.open()
        result: str = await hold.run(once)
        assert hold.reestablished == 1
        assert hold.session_id == "session-1"
        await hold.close()
        return result

    assert asyncio.run(drive()) == "delivered"
    assert calls == ["session-0", "session-1"]
    assert opened[0].closed and opened[1].closed


def test_a_second_disowned_session_is_not_chased_for_ever() -> None:
    """One re-establishment per request; a peer that keeps disowning us surfaces."""
    hold = HeldSession(OpenedSession)

    async def always(_: object) -> object:
        raise session_gone()

    async def drive() -> None:
        await hold.open()
        await hold.run(always)

    with pytest.raises(McpError):
        asyncio.run(drive())
    assert hold.reestablished == 1


def test_a_failure_while_opening_leaves_nothing_held() -> None:
    """A half-open session is worse than none: the stack unwinds and the id is None."""

    def refuse() -> OpenedSession:
        raise ConnectionRefusedError("the peer is not listening")

    hold = HeldSession(refuse)
    with pytest.raises(ConnectionRefusedError):
        asyncio.run(hold.open())
    assert not hold.held and hold.session_id is None
