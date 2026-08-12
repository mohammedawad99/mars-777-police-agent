"""Real compositions bound to OS-assigned ports, plus a truthful launch document.

The subprocess helpers live here because they are mechanics, not assertions: how
to start the executable on either platform, how to know its *application* is
answering, and how to ask it to stop the way an operator would.
"""

import http.client
import json
import os
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path

import composed_builders as compose
from r16_builders import GROUP_A, GROUP_B

from mars777_police.agent_runtime import AgentRuntime
from mars777_police.app.sealed_record_values import ActorRole
from mars777_police.composition_values import AgentComposition
from mars777_police.transport.codec_auth import encode_profiles
from mars777_police.transport.codec_declaration import encode_declaration

HOST = "127.0.0.1"
MCP_PATH = "/mcp"
SECRET = "out-of-band-provisioned-secret"
"""A synthetic test key; the real one never appears in this repository."""

WINDOWS = sys.platform == "win32"
"""Windows has no SIGINT to deliver to a child; it has console control events."""

GROUP_FLAG = subprocess.CREATE_NEW_PROCESS_GROUP if WINDOWS else 0
"""A control event reaches only a child in its own group; POSIX passes 0."""

STOP_EVENT = signal.CTRL_BREAK_EVENT if WINDOWS else signal.SIGINT
"""An operator's stop: Ctrl-C on POSIX, Ctrl-Break on Windows."""

NOT_ACCEPTABLE = 406
"""FastMCP's answer to a plain GET - the ASGI stack replying, not the kernel."""

READY_TIMEOUT = 30.0
POLL_SECONDS = 0.05


def spawn(package: str, launch: Path, environment: dict[str, str]) -> "subprocess.Popen[str]":
    """Start the real executable, in its own process group where that is needed."""
    return subprocess.Popen(
        [sys.executable, "-m", package, "--launch", str(launch)],
        env={**os.environ, **environment},
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        creationflags=GROUP_FLAG,
    )


def await_application(child: "subprocess.Popen[str]", port: int) -> int:
    """Return the status of the first HTTP response the **application** produced.

    A TCP connect proves nothing here. R6 binds and listens itself, so the kernel
    accepts into the backlog while no server exists yet and holds the request
    unanswered until one does - a plain connect therefore succeeds long before
    FastMCP can be interrupted gracefully, which is exactly the window that made
    CI red. Only a parsed status line proves the ASGI stack is running.
    """
    deadline = time.monotonic() + READY_TIMEOUT
    while time.monotonic() < deadline:
        if child.poll() is not None:
            raise AssertionError(f"the agent exited early: {child.communicate()[1]}")
        connection = http.client.HTTPConnection(HOST, port, timeout=1.0)
        try:
            connection.request("GET", MCP_PATH)
            return int(connection.getresponse().status)
        except (OSError, http.client.HTTPException):
            time.sleep(POLL_SECONDS)
        finally:
            connection.close()
    raise AssertionError("the agent never answered an HTTP request")


def free_port() -> int:
    """Ask the OS for a port rather than guessing one."""
    with socket.socket() as probe:
        probe.bind((HOST, 0))
        return int(probe.getsockname()[1])


def runtime_for(composition: AgentComposition, port: int | None = None) -> AgentRuntime:
    """The production lifecycle owner over a real composition."""
    return AgentRuntime(composition, HOST, port if port is not None else free_port())


def agent(
    group_id: str = GROUP_A,
    slot: str = "group_a",
    role: ActorRole = ActorRole.POLICE,
    opponent: str = "http://127.0.0.1:1/mcp",
) -> AgentComposition:
    """One real composed agent pointed at *opponent*."""
    return compose.compose(group_id, slot, role, opponent)


def pair_urls() -> tuple[int, int]:
    """Two ports chosen before either agent is composed."""
    return free_port(), free_port()


def launch_document(group_id: str = GROUP_A, slot: str = "group_a") -> str:
    """A launch document in the exact frozen wire shapes, from real values."""
    identity = compose.identity_for(group_id, slot)
    return json.dumps(
        {
            "declaration": encode_declaration(identity.declaration).model_dump(
                mode="json", exclude_none=True
            ),
            "profiles": encode_profiles(identity.profiles).model_dump(mode="json"),
            "first_sub_game": identity.first_sub_game,
        }
    )


def written_launch(directory: Path, group_id: str = GROUP_A, slot: str = "group_a") -> Path:
    """Write the launch document a subprocess can be started with."""
    path = directory / "launch.json"
    path.write_text(launch_document(group_id, slot), encoding="utf-8")
    return path


def other() -> tuple[str, str, ActorRole]:
    """The opposing side's identity."""
    return GROUP_B, "group_b", ActorRole.THIEF
