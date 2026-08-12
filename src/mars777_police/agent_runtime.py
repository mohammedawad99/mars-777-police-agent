"""Making the composed agent live, and putting it away again.

Stage 5-R5 built the object graph and started nothing. This starts it: the server
listens, the composed `PeerClient` holds its session, both undone in reverse.

**Readiness is a bound socket, not a delay.** We bind it ourselves and hand it to
`run_http_async`, so "address already in use" raises in *this* frame, and a peer
connecting the instant `serve` returns is queued by the kernel. One scheduling
turn - not a sleep - then lets a server that dies in its first step say so,
instead of `SERVING` being reported over a corpse.

**Serving and connecting are separate, because the API made them so.**
`PeerClient.__aenter__` opens a real connection, so it cannot succeed until the
opponent is listening - welded together, two agents could never boot each other.
No Step-0 is sent; and if the client fails, the server stops before it escapes.
"""

import asyncio
import socket
from contextlib import suppress
from dataclasses import dataclass, field
from enum import StrEnum

from .app.protocol_errors import LocalDefectError
from .composition_values import AgentComposition

BACKLOG = 128
"""Pending connections the kernel holds before the server accepts them."""


async def release(task: asyncio.Task[None] | None, listener: socket.socket | None) -> None:
    """Stop a served ingress, tolerating a partially-started one.

    Either may be absent: cleanup must be callable from every point a startup can
    fail at. The socket closes in a `finally` - uvicorn never closes one it was
    handed - and only `CancelledError` is swallowed, so a task that died of
    anything else still raises here."""
    try:
        if task is not None:
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task
    finally:
        if listener is not None:
            listener.close()


class RuntimeState(StrEnum):
    """The agent process lifecycle, in the one order it runs."""

    NEW = "NEW"
    SERVING = "SERVING"
    RUNNING = "RUNNING"
    CLOSED = "CLOSED"


@dataclass(slots=True)
class AgentRuntime:
    """One composed agent, started and stopped as a unit."""

    composition: AgentComposition
    host: str
    port: int
    path: str = field(default="/mcp")
    state: RuntimeState = field(default=RuntimeState.NEW)
    server_task: asyncio.Task[None] | None = field(default=None)
    listener: socket.socket | None = field(default=None)

    def _listen(self) -> socket.socket:
        """Bind now, so a port conflict fails before anything starts."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.bind((self.host, self.port))
            sock.listen(BACKLOG)
        except BaseException:
            sock.close()
            raise
        return sock

    async def serve(self) -> None:
        """Bring up our inbound ingress, or fail with the reason it did not: one
        `asyncio.wait(timeout=0)` turn is all a doomed server needs to have died."""
        if self.state is not RuntimeState.NEW:
            raise LocalDefectError(f"an agent runtime cannot serve while {self.state.value}")
        listener = self._listen()
        port = listener.getsockname()[1]
        serving = self.composition.server.run_http_async(
            show_banner=False, host=self.host, port=port, path=self.path, sockets=[listener]
        )
        task = asyncio.create_task(serving)
        await asyncio.wait((task,), timeout=0)
        if task.done():
            await release(task, listener)
            raise LocalDefectError("the inbound server stopped before it served")
        self.server_task, self.listener, self.state = task, listener, RuntimeState.SERVING

    async def connect(self) -> None:
        """Hold one persistent outbound session open to the opponent."""
        if self.state is not RuntimeState.SERVING:
            raise LocalDefectError(f"an agent runtime cannot connect while {self.state.value}")
        try:
            await self.composition.peer_client.__aenter__()
        except BaseException:
            await self.stop()
            raise
        self.state = RuntimeState.RUNNING

    async def start(self) -> None:
        """Serve the ingress, then hold the outbound session open."""
        await self.serve()
        await self.connect()

    async def wait_closed(self) -> None:
        """Wait until the served ingress ends - a Ctrl-C makes the server, which
        installs its own interrupt handling, return normally and shut down quietly."""
        task = self.server_task
        if task is None:
            raise LocalDefectError("the runtime is not serving")
        with suppress(asyncio.CancelledError):
            await task

    async def stop(self) -> None:
        """Release the session, then the ingress. Safe to call twice."""
        if self.state not in (RuntimeState.SERVING, RuntimeState.RUNNING):
            return
        connected = self.state is RuntimeState.RUNNING
        task, listener = self.server_task, self.listener
        self.server_task, self.listener, self.state = None, None, RuntimeState.CLOSED
        try:
            if connected:
                await self.composition.peer_client.__aexit__(None, None, None)
        finally:
            await release(task, listener)

    @property
    def address(self) -> str:
        """The ingress this runtime is serving, once it is bound."""
        if self.listener is None:
            raise LocalDefectError("the runtime is not serving")
        host, port = self.listener.getsockname()[:2]
        return f"http://{host}:{port}{self.path}"

    async def __aenter__(self) -> "AgentRuntime":
        """Start, and hand back a running agent."""
        await self.start()
        return self

    async def __aexit__(self, kind: object, value: object, traceback: object) -> None:
        """Stop, whatever happened inside."""
        await self.stop()
