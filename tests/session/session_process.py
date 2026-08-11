"""Launch the production peer as a genuinely independent OS process."""

import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from types import TracebackType

from peer_process import free_port

READY_TIMEOUT = 30.0


class SessionPeer:
    """The R3R peer server, with bounded startup and guaranteed teardown."""

    def __init__(self) -> None:
        self.port = free_port()
        self._process: subprocess.Popen[bytes] | None = None

    @property
    def url(self) -> str:
        """This peer's stable group-level ingress."""
        return f"http://127.0.0.1:{self.port}/mcp"

    def __enter__(self) -> "SessionPeer":
        script = Path(__file__).with_name("session_peer.py")
        self._process = subprocess.Popen(
            [sys.executable, str(script), str(self.port)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        self._await_ready()
        return self

    def _await_ready(self) -> None:
        deadline = time.monotonic() + READY_TIMEOUT
        while time.monotonic() < deadline:
            try:
                urllib.request.urlopen(self.url, timeout=1)
            except urllib.error.HTTPError:
                return
            except Exception:
                time.sleep(0.1)
            else:
                return
        raise RuntimeError("the production peer never became ready")

    def __exit__(
        self,
        kind: type[BaseException] | None,
        value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        process = self._process
        if process is not None:
            process.terminate()
            process.wait(timeout=10)
