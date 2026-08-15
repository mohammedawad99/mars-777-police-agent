"""Making the composed agent live, and putting it away again.

Stage 5-R5 built the object graph and started nothing. This starts it: the
server listens, the `PeerClient` holds its session, both undone in reverse.
**Readiness is a bound socket, not a delay.** We bind it ourselves and hand it
to `run_http_async`, so "address already in use" raises in *this* frame, a peer
connecting the instant `serve` returns is queued by the kernel, and one
scheduling turn lets a server that dies in its first step say so.

**Serving and connecting are separate, because the API made them so.**
`PeerClient.__aenter__` opens a real connection, so it cannot succeed until the
opponent is listening - welded together, two agents could never boot each other.
`connect` keeps its one-shot contract; `connect_until_ready` is the startup
variant, and reopens only the session."""

import asyncio
import socket
from contextlib import suppress
from dataclasses import dataclass, field
from enum import StrEnum

from .app.protocol_errors import LocalDefectError
from .composition_values import AgentComposition
from .ingress_release import close_session, release
from .startup_budget import StartupBudget

BACKLOG = 128
"""Pending connections the kernel holds before the server accepts them."""


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
        """Bring up our inbound ingress: one `asyncio.wait(timeout=0)` turn is all a
        doomed server needs to have died in."""
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

    async def _open_session(self) -> None:
        """The one call that establishes the outbound session, and nothing else."""
        await self.composition.peer_client.__aenter__()

    async def connect(self) -> None:
        """Hold one persistent outbound session open to the opponent - one attempt."""
        if self.state is not RuntimeState.SERVING:
            raise LocalDefectError(f"an agent runtime cannot connect while {self.state.value}")
        try:
            await self._open_session()
        except BaseException:
            await self.stop()
            raise
        self.state = RuntimeState.RUNNING

    async def connect_until_ready(self, budget: StartupBudget) -> None:
        """Connect, tolerating a peer that has not started listening **yet**. The
        failure path is deliberately `connect`'s: stopped, and the last failure
        escapes."""
        if self.state is not RuntimeState.SERVING:
            raise LocalDefectError(f"an agent runtime cannot connect while {self.state.value}")
        try:
            await budget.keep_trying(self._open_session)
        except BaseException:
            await self.stop()
            raise
        self.state = RuntimeState.RUNNING

    async def start(self) -> None:
        """Serve the ingress, then hold the outbound session open."""
        await self.serve()
        await self.connect()

    async def wait_closed(self) -> None:
        """Wait until the served ingress ends - the server installs its own
        interrupt handling, so a Ctrl-C returns normally here."""
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
                await close_session(self.composition.peer_client)
        finally:
            await release(task, listener)

    @property
    def address(self) -> str:
        """The ingress this runtime serves, once bound."""
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
