"""The live peer process: one real FastMCP server running production runtimes."""

import subprocess
import sys
from pathlib import Path

from peer_process import PeerProcess


class LivePeerProcess(PeerProcess):
    """A `PeerProcess` whose child serves `LiveOperations` and writes a status file."""

    def __init__(self, port: int, status: Path) -> None:
        super().__init__("MaRs-777", port=port)
        self.status = status

    def _command(self) -> list[str]:
        script = Path(__file__).with_name("live_entrypoint.py")
        return [sys.executable, str(script), str(self.port), str(self.status)]

    def received(self) -> list[str]:
        """The operation names the remote application actually handled, in order."""
        import json

        return list(json.loads(self.status.read_text(encoding="utf-8"))["seen"])

    def state(self) -> dict[str, object]:
        """The remote peer's self-reported production state."""
        import json

        loaded: dict[str, object] = json.loads(self.status.read_text(encoding="utf-8"))
        return loaded

    def __repr__(self) -> str:
        return f"LivePeerProcess(port={self.port})"


__all__ = ["LivePeerProcess", "subprocess"]
