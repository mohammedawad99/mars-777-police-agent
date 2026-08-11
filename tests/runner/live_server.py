"""A real FastMCP server in this process, so a test can hold both sides.

Stage 5-R4 needs the *callback* topology: A sends a commitment, B's inbound
server accepts it, B's runner acknowledges, A's inbound server accepts that.
Both sides therefore have to be reachable over real HTTP while their runtimes
stay inspectable, which a subprocess cannot give. uvicorn runs in a thread; the
transport, the sessions and the servers are all production.
"""

import threading
import time

import uvicorn
from peer_process import free_port

from mars777_police.transport.peer_operations import InboundPeerOperations
from mars777_police.transport.server import build_server

READY_TIMEOUT = 15.0


class LiveServer:
    """One production peer server, served in a background thread."""

    def __init__(self, operations: InboundPeerOperations, name: str) -> None:
        self.port = free_port()
        application = build_server(operations, name=name).http_app(path="/mcp")
        config = uvicorn.Config(application, host="127.0.0.1", port=self.port, log_level="error")
        self._server = uvicorn.Server(config)
        self._thread = threading.Thread(target=self._server.run, daemon=True)

    @property
    def url(self) -> str:
        """This peer's stable ingress."""
        return f"http://127.0.0.1:{self.port}/mcp"

    def __enter__(self) -> "LiveServer":
        self._thread.start()
        deadline = time.monotonic() + READY_TIMEOUT
        while not self._server.started and time.monotonic() < deadline:
            time.sleep(0.05)
        if not self._server.started:
            raise RuntimeError("the production server never became ready")
        return self

    def __exit__(self, kind: object, value: object, traceback: object) -> None:
        self._server.should_exit = True
        self._thread.join(timeout=10)
