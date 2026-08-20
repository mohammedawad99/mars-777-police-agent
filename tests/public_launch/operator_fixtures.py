"""The stand-ins a public run needs: ports, recorders, an environment, a document.

Every one of these is a local double for something a real match supplies - a
free private port, a role backend that only records what it was asked, the
gateway's loopback settlement surface, the operator environment, and the launch
document a KIT friendly needs. None of them asserts anything; they exist so the
wiring tests can be about wiring.
"""

import json
import socket
import threading
import time
from pathlib import Path

import pytest
import uvicorn
from executable_process import environment, launch_document
from fastmcp import FastMCP


def free_port() -> int:
    held = socket.socket()
    held.bind(("127.0.0.1", 0))
    port = int(held.getsockname()[1])
    held.close()
    return port


def recorder(port: int, seen: list[str]) -> uvicorn.Server:
    """A private local stand-in for one role backend."""
    app: FastMCP = FastMCP("recorder")

    @app.tool
    async def negotiate(message: dict[str, object]) -> dict[str, bool]:
        seen.append("negotiate")
        return {"ok": True}

    config = uvicorn.Config(
        app.http_app(path="/mcp"), host="127.0.0.1", port=port, log_level="error"
    )
    server = uvicorn.Server(config)
    threading.Thread(target=server.run, daemon=True).start()
    while not server.started:
        time.sleep(0.05)
    return server


def operator_env(monkeypatch: pytest.MonkeyPatch, root: Path) -> None:
    for name, value in environment(root=root).items():
        monkeypatch.setenv(name, value)


def kit_launch_document(root: Path) -> Path:
    """The counted launch document plus the flat terms a KIT pairing agreed."""
    document = json.loads(launch_document())
    document["kit_terms"] = {"board_size": 7, "max_steps": 35}
    path = root / "launch.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    return path


def admin_server(port: int, seen: list[int]) -> uvicorn.Server:
    """A private stand-in for the gateway's loopback settlement surface."""
    app: FastMCP = FastMCP("admin")

    @app.tool
    async def sub_game_settled(sub_game: int) -> dict[str, bool]:
        seen.append(sub_game)
        return {"ok": True}

    config = uvicorn.Config(
        app.http_app(path="/mcp"), host="127.0.0.1", port=port, log_level="error"
    )
    server = uvicorn.Server(config)
    threading.Thread(target=server.run, daemon=True).start()
    while not server.started:
        time.sleep(0.05)
    return server


def empty_chain() -> object:
    from mars777_police.app.commitment_codecs import CommitmentCodec
    from mars777_police.app.kit_records import KitRecordChain
    from mars777_police.protocol.secure_nonce import SecretsNonceSource

    return KitRecordChain(CommitmentCodec.KIT_CORE_COMMITMENT_V1, SecretsNonceSource())
