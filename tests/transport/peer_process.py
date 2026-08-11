"""Launch one peer as a genuinely independent OS process.

Not two server objects in one interpreter: a real `subprocess` with its own
memory, its own application runtime and its own port, reachable only over
Streamable HTTP. Anything less would let a shared object hide a transport bug.

Windows-compatible by construction - `subprocess` with a spawn-safe entrypoint,
no `fork`, no Unix socket, no signal semantics, and every wait bounded.
"""

import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from types import TracebackType

READY_TIMEOUT = 30.0
SHUTDOWN_TIMEOUT = 10.0


def free_port() -> int:
    """Ask the OS for an unused port instead of hard-coding a racy constant."""
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return int(probe.getsockname()[1])


class PeerProcess:
    """A peer server in its own process, with bounded startup and cleanup."""

    def __init__(self, group_id: str, port: int | None = None) -> None:
        self.group_id = group_id
        self.port = port or free_port()
        self._process: subprocess.Popen[bytes] | None = None

    @property
    def url(self) -> str:
        """This peer's stable group-level ingress."""
        return f"http://127.0.0.1:{self.port}/mcp"

    def _command(self) -> list[str]:
        """The child command line; subclasses vary only this."""
        script = Path(__file__).with_name("peer_entrypoint.py")
        return [sys.executable, str(script), self.group_id, str(self.port)]

    def __enter__(self) -> "PeerProcess":
        self._process = subprocess.Popen(
            self._command(), stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        self._await_ready()
        return self

    def __exit__(
        self,
        kind: type[BaseException] | None,
        value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Always terminate, even when the test failed - no orphan servers."""
        process = self._process
        if process is None:
            return
        process.terminate()
        try:
            process.wait(timeout=SHUTDOWN_TIMEOUT)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=SHUTDOWN_TIMEOUT)

    def _await_ready(self) -> None:
        """Poll the real endpoint rather than sleeping and hoping."""
        deadline = time.monotonic() + READY_TIMEOUT
        while time.monotonic() < deadline:
            if self._process is not None and self._process.poll() is not None:
                raise RuntimeError(f"peer {self.group_id} exited during startup")
            try:
                urllib.request.urlopen(self.url.replace("/mcp", "/"), timeout=1.0)
            except urllib.error.HTTPError:
                return
            except OSError:
                time.sleep(0.05)
        raise TimeoutError(f"peer {self.group_id} was not ready within {READY_TIMEOUT}s")


class CadencePeer(PeerProcess):
    """A cadence peer: its own runtime, its own port, its own status file.

    The status file is **harness-owned test IPC**, not a peer surface: the four
    public MCP tools are unchanged, and nothing here is reachable by a peer.
    """

    def __init__(self, group_id: str, status: Path, base: int = 100) -> None:
        super().__init__(group_id)
        self.status = status
        self.base = base

    def _command(self) -> list[str]:
        script = Path(__file__).with_name("cadence_entrypoint.py")
        return [
            sys.executable,
            str(script),
            self.group_id,
            str(self.port),
            str(self.status),
            str(self.base),
        ]
