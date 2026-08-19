"""Standing one FastMCP app up on a port we bound ourselves, and taking it down.

Framework mechanics, so they live in `transport` with the rest of it: the four
layers inward of the adapter stay testable and portable without FastMCP, and a
lifecycle owner outside this package should not have to name it to serve.

**Bind first, serve second.** Binding ourselves means "address already in use"
raises in the caller's frame rather than inside a server task nobody is
awaiting, a peer connecting the instant we return is queued by the kernel, and
one scheduling turn is enough for a server that dies immediately to say so.
"""

import asyncio
import socket
from dataclasses import dataclass

from fastmcp import FastMCP

BACKLOG = 128
"""Pending connections the kernel holds before the server accepts them."""


@dataclass(frozen=True, slots=True)
class ServedHttp:
    """One served app: the task running it and the listener it was given."""

    task: asyncio.Task[None]
    listener: socket.socket

    @property
    def port(self) -> int:
        """The port actually bound, which is what an ephemeral request returns."""
        return int(self.listener.getsockname()[1])


async def serve_http(server: FastMCP, host: str, port: int, path: str = "/mcp") -> ServedHttp:
    """Bind *port*, serve *server* over it, and hand back both resources."""
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        listener.bind((host, port))
        listener.listen(BACKLOG)
    except BaseException:
        listener.close()
        raise
    bound = int(listener.getsockname()[1])
    task = asyncio.create_task(
        server.run_http_async(
            show_banner=False, host=host, port=bound, path=path, sockets=[listener]
        )
    )
    await asyncio.wait((task,), timeout=0)
    return ServedHttp(task, listener)
