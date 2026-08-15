"""Putting a live agent away: the held session first, then the served ingress.

Serving is two resources acquired in order - a bound listener, then the task
running the ASGI server over it - and every failure path has to release
whichever of them exists. That is a different concern from the lifecycle that
acquires them, and it is the one piece `AgentRuntime` needs identically in
`serve`'s failure branch and in `stop`.

**One teardown failure is the sound of a session ending, not of one failing.**
When a run is over, Windows' IOCP proactor aborts the outstanding operations of
the session being closed and reports `WinError 995`. The series has already
finished by then - every artifact written, the result agreed - so letting that
turn a completed run into a failed process would be a lie about what happened.
It is recognised by the verified error number and by nothing else: no platform
test, no error class, no message. An `OSError` without a `winerror` is never
benign, which is every `OSError` outside Windows.
"""

import asyncio
import socket
from contextlib import suppress

from .transport.client import PeerClient

SESSION_ABORTED = 995
"""`WinError 995` - the I/O operation was aborted by a thread or process exit."""


async def release(task: asyncio.Task[None] | None, listener: socket.socket | None) -> None:
    """Stop a served ingress, tolerating a partially-started one.

    Either may be absent: cleanup must be callable from every point a startup
    can fail at, and only `CancelledError` is swallowed."""
    try:
        if task is not None:
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task
    finally:
        if listener is not None:
            listener.close()


async def close_session(client: PeerClient) -> None:
    """Exit the held outbound session, tolerating only the terminal abort above.

    Every other failure - an auth, protocol or transport fault, or any other
    `OSError` - still leaves this frame, so a session that broke for a reason
    the caller should hear about is still heard.
    """
    try:
        await client.__aexit__(None, None, None)
    except OSError as failure:
        if getattr(failure, "winerror", None) != SESSION_ABORTED:
            raise
