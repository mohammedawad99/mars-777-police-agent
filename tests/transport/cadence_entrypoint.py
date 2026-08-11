"""Child-process entrypoint for a cadence peer: one runtime, one server, one port.

Guarded under `__main__` for Windows spawn. Each process builds its **own**
`CadenceOperations`; the only thing crossing between them is FastMCP HTTP, and
the only thing crossing to the harness is a status file this process writes.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "protocol"))
sys.path.insert(0, str(Path(__file__).resolve().parent))


def main(group_id: str, port: int, status: str, base: int) -> None:
    """Serve one cadence peer until terminated."""
    import uvicorn
    from cadence_ops import CadenceOperations

    from mars777_police.transport.server import build_server

    operations = CadenceOperations(group_id, Path(status), base)
    application = build_server(operations, name=f"cadence-{group_id}").http_app(path="/mcp")
    uvicorn.run(application, host="127.0.0.1", port=port, log_level="error")


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]), sys.argv[3], int(sys.argv[4]))
