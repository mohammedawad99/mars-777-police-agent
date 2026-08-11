"""Child-process entrypoint for the live public peer.

Guarded under `__main__` for Windows spawn. The process owns its own runtimes;
the only things crossing out of it are FastMCP responses and the status file it
writes itself.
"""

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "transport"))
sys.path.insert(0, str(HERE))


def main(port: int, status: str) -> None:
    """Serve one live peer until terminated."""
    import uvicorn
    from live_ops import LiveOperations

    from mars777_police.transport.server import build_server

    operations = LiveOperations(Path(status))
    application = build_server(operations, name="live-peer").http_app(path="/mcp")
    uvicorn.run(application, host="127.0.0.1", port=port, log_level="error")


if __name__ == "__main__":
    main(int(sys.argv[1]), sys.argv[2])
