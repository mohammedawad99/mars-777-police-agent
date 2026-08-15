"""Putting a served ingress away, from any point its startup reached.

Serving is two resources acquired in order - a bound listener, then the task
running the ASGI server over it - and every failure path has to release
whichever of them exists. That is a different concern from the lifecycle that
acquires them, and it is the one piece `AgentRuntime` needs identically in
`serve`'s failure branch and in `stop`.
"""

import asyncio
import socket
from contextlib import suppress


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
