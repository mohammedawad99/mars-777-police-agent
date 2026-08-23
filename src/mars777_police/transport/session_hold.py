"""One held outbound session, and the single condition under which it is remade.

**Why a held session can be dead before its first protocol request.** The
session is opened during startup - `session_deadline` says so and the boot gate
depends on it, because a process that could not dial its opponent has no way to
prove the opponent is up. But startup is not kickoff. Between the two the peer's
own runner may restart, its public tunnel may be re-established, or its server
may retire an idle session. The session id we hold then names nothing, and the
first real request of the series is the one that discovers it.

**The one condition.** A Streamable-HTTP server that answers a POST with
HTTP 404 is stating that it has no such session, so it did not route that body
to a tool. The MCP client turns exactly that answer - and nothing else - into
`Session terminated`, so the code below can tell "never dispatched" apart from
"dispatched, outcome unknown" without guessing.

**What this is not.** It is not a retry. A request that reached the peer's
dispatcher is never re-issued here, whatever it failed with: whether a
commitment arrived is unknowable at this layer, and that refusal is the whole
reason `E-TRANSPORT` is terminal. Re-establishing a session the server never
had is the lifecycle action `startup_budget` already names - nothing has been
agreed, no commitment exists, and the only thing redone is opening the session.

The remade session is a *new* session: a fresh `initialize`, a fresh id. An id
the server has retired is never sent again.

**One session per peer lifecycle, not one per operation**, which is measured:
over a real public tunnel 30 operations each opening their own session failed
from the twenty-first onward, while the same 30 in one held session all
succeeded. Re-establishing on a disowned id keeps that property - it replaces
the one session, it does not start opening one per call.
"""

import logging
from collections.abc import Awaitable, Callable
from contextlib import AsyncExitStack
from typing import Any

from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport
from mcp.shared.exceptions import McpError

from ..app.protocol_errors import LocalDefectError

SESSION_NOT_FOUND_CODE = 32600
"""The code the MCP client stamps on the error it raises for a POST 404."""

SESSION_NOT_FOUND_TEXT = "session terminated"
"""Its message, lowercased. One emitter in the client, one cause: HTTP 404."""

Session = Client[StreamableHttpTransport]
Call = Callable[[Session], Awaitable[Any]]

log = logging.getLogger(__name__)


def session_not_found(failure: BaseException) -> bool:
    """True only when the peer answered that it has no such session.

    Both the code and the text are required. If either moves in a future client
    the answer is False, this falls back to today's behaviour - one terminal
    `E-TRANSPORT` - and a pinned test says which half drifted.
    """
    if not isinstance(failure, McpError):
        return False
    error = failure.error
    return error.code == SESSION_NOT_FOUND_CODE and (
        str(error.message).strip().lower() == SESSION_NOT_FOUND_TEXT
    )


class HeldSession:
    """One session to one peer, remade only when the server had no such session."""

    def __init__(self, open_session: Callable[[], Session]) -> None:
        self._open = open_session
        self._stack: AsyncExitStack | None = None
        self._session: Session | None = None
        self.reestablished = 0
        """How many times the peer proved our id was unknown to it."""

    @property
    def held(self) -> bool:
        """Whether a session is currently open, so callers keep one code path."""
        return self._session is not None

    @property
    def session_id(self) -> str | None:
        """The id now in use, for evidence and for a peer's interop report."""
        if self._session is None:
            return None
        identifier: str | None = self._session.transport.get_session_id()
        return identifier

    async def open(self) -> None:
        """Open the one session, releasing the stack if opening itself fails."""
        stack = AsyncExitStack()
        try:
            self._session = await stack.enter_async_context(self._open())
        except BaseException:
            await stack.aclose()
            raise
        self._stack = stack
        log.info("outbound session opened id=%s", self.session_id)

    async def close(self) -> None:
        """Close the held session exactly once, whatever happened inside."""
        stack, self._stack, self._session = self._stack, None, None
        if stack is not None:
            await stack.aclose()

    async def run(self, call: Call) -> Any:
        """Run *call* in the held session, remaking it only on a 404 session.

        The second attempt is made against a session the peer has just issued,
        and it is attempted **only** because the peer stated it never saw the
        first one. Anything else leaves this frame untouched.
        """
        session = self._require()
        try:
            return await call(session)
        except McpError as failure:
            if not session_not_found(failure):
                raise
            retired = self.session_id
        await self._remake(retired)
        return await call(self._require())

    async def _remake(self, retired: str | None) -> None:
        """Discard the session the peer disowned and open a fresh one."""
        log.warning("peer has no session id=%s; opening a new one", retired)
        await self.close()
        await self.open()
        self.reestablished += 1

    def _require(self) -> Session:
        if self._session is None:
            raise LocalDefectError("no outbound session is held; open one before calling")
        return self._session
