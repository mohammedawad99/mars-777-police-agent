"""The child-process entrypoint: one peer, one server, one port.

Guarded under `__main__` so Windows' spawn start method re-imports it safely.
Each process builds its **own** application runtime; nothing is shared with the
parent or the other peer except the HTTP endpoint itself.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "protocol"))
sys.path.insert(0, str(Path(__file__).resolve().parent))


def main(group_id: str, port: int) -> None:
    """Serve one peer until terminated."""
    import uvicorn
    from peer_recorder import RecordingOperations

    from mars777_police.transport.server import build_server

    operations = RecordingOperations()
    application = build_server(operations, name=f"peer-{group_id}").http_app(path="/mcp")
    uvicorn.run(application, host="127.0.0.1", port=port, log_level="error")


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]))
