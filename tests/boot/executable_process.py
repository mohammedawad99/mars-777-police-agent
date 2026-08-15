"""Running the real executable from a test, and judging how it stopped.

Everything here exists for one consumer - the `python -m` tests - and it is all
mechanics rather than assertions: how to start the process on either platform,
how to know its *application* is answering rather than just its socket, what an
operator's stop looks like, and what "cleanly" means on the platform running.

The launch document and operator environment live here too, because a subprocess
is the only thing that needs them written to disk and exported.
"""

import http.client
import json
import os
import re
import signal
import subprocess
import sys
import time
from pathlib import Path

import composed_builders as compose
import r7_builders as r7
from boot_builders import HOST, SECRET, free_port
from r16_builders import GROUP_A

from mars777_police import __main__ as entry
from mars777_police.transport.codec_auth import encode_profiles
from mars777_police.transport.codec_config import encode_config
from mars777_police.transport.codec_declaration import encode_declaration

MCP_PATH = "/mcp"

WINDOWS = sys.platform == "win32"
"""Windows has no SIGINT to deliver to a child; it has console control events."""

GROUP_FLAG = subprocess.CREATE_NEW_PROCESS_GROUP if WINDOWS else 0
"""A control event reaches only a child in its own group; POSIX passes 0."""

STOP_EVENT = signal.CTRL_BREAK_EVENT if WINDOWS else signal.SIGINT
"""An operator's stop: Ctrl-C on POSIX, Ctrl-Break on Windows."""

NOT_ACCEPTABLE = 406
"""FastMCP's answer to a plain GET - the ASGI stack replying, not the kernel."""

GRACEFUL_MARKERS = ("Shutting down", "Application shutdown complete", "Finished server process")
"""Uvicorn's own record: shutdown begun, application finished, process finished."""

CONTROL_EXIT = 3
"""The status Windows reports after a console control event. It is **not** a
success code: it is accepted only together with the whole record above."""

READY_TIMEOUT = 30.0
POLL_SECONDS = 0.05


def spawn(package: str, launch: Path, environ: dict[str, str]) -> "subprocess.Popen[str]":
    """Start the real executable, in its own process group where that is needed."""
    return subprocess.Popen(
        [sys.executable, "-m", package, "--launch", str(launch)],
        env={**os.environ, **environ},
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        creationflags=GROUP_FLAG,
    )


def spawn_opponent(
    role: str, port: int, opponent_url: str, root: Path, variant: str = "same"
) -> "subprocess.Popen[str]":
    """Start the **synthetic, non-counted** distinct-group opponent process.

    A separate OS process with its own memory, its own artifact root and its own
    `SeriesDriver`. It is not a league participant and its result is not match
    evidence; it exists so the shipped CLI has a lawful counterparty to boot
    against without weakening anti-self-play.
    """
    script = Path(__file__).with_name("opponent_entrypoint.py")
    return subprocess.Popen(
        [sys.executable, str(script), role, str(port), opponent_url, str(root), variant],
        env={**os.environ},
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        creationflags=GROUP_FLAG,
    )


def official(root: Path) -> list[str]:
    """The official file names a finished side left behind, sorted."""
    return sorted(path.name for path in root.iterdir()) if root.exists() else []


def await_application(child: "subprocess.Popen[str]", port: int) -> int:
    """Return the status of the first HTTP response the **application** produced.

    A TCP connect proves nothing: R6 binds and listens itself, so the kernel
    accepts into the backlog while no server exists and holds the request
    unanswered - which is the window that made CI red. Only a parsed status line
    proves the ASGI stack is running.
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


CONNECTION_REPORT = (
    "mars777_police.transport.wire_errors.TransportFailureError",
    "httpx.ConnectError",
    "RuntimeError: Client failed to connect",
    "ConnectionRefusedError",
    "OSError",
    "asyncio.exceptions.CancelledError",
    "anyio.WouldBlock",
    "ExceptionGroup",
    "BaseExceptionGroup",
)
"""The exception names one *failed connection attempt* prints, and no others.

A process that starts before its opponent fails to connect on purpose and
retries; the FastMCP client logs each attempt in full, chained down to the
`E-TRANSPORT` this repository translates it into. Those lines are the peer's
absence being reported, so `crashed` names them explicitly rather than matching
the word "Traceback" - which appears in both a report and a real crash.

**Only the startup tests may use this.** `assert_clean_operator_stop` keeps the
stricter rule, because an operator's Ctrl-C is not supposed to produce any
traceback at all and weakening that would hide a real one.
"""

FAILURE = re.compile(r"^(?:\s*\+?\s*)([A-Za-z_][\w.]*(?:Error|Exception|Group))\b")
"""The name at the head of an exception line, indented inside a group or not."""


def crashed(err: str) -> bool:
    """True when *err* names an exception that is not a connection report."""
    for line in err.splitlines():
        found = FAILURE.match(line)
        if found and not any(known in line for known in CONNECTION_REPORT):
            return True
    return False


def assert_clean_operator_stop(status: int, out: str, err: str, windows: bool = WINDOWS) -> None:
    """Assert the stop was clean under *this platform's* contract.

    POSIX is exactly 0 - a control-event status there would be a real failure.
    Windows delivers `CTRL_BREAK_EVENT` through the console, which terminates the
    process on its own terms after the handlers run, so the status alone cannot
    tell a graceful shutdown from a kill; the server's own shutdown record is
    what does, and 3 is refused without it.
    """
    assert "Traceback" not in err, err
    assert SECRET not in out and SECRET not in err
    if not windows:
        assert status == 0, err
        return
    assert status in {0, CONTROL_EXIT}, err
    missing = [marker for marker in GRACEFUL_MARKERS if marker not in err]
    assert not missing, f"status {status} without a complete shutdown, missing {missing}: {err}"


def environment(
    port: int = 0, root: Path | None = None, opponent: str | None = None
) -> dict[str, str]:
    """A synthetic operator environment; never the real one.

    The role comes from the entrypoint this repository ships, so the one file
    serves both repositories without naming a side. The artifact root is local
    filesystem config and each process is given its own.
    """
    return {
        "MARS777_ROLE": entry.ROLE.value,
        "MARS777_BIND_HOST": HOST,
        "MARS777_BIND_PORT": str(port or free_port()),
        "MARS777_KEY_ID": "mars777-k1",
        "MARS777_AUTH_SECRET": SECRET,
        "MARS777_ARTIFACT_ROOT": str(root if root is not None else Path.cwd()),
        "MARS777_OPPONENT_ENDPOINT": opponent or f"http://{HOST}:{free_port()}{MCP_PATH}",
    }


def launch_document(group_id: str = GROUP_A, slot: str = "group_a") -> str:
    """A launch document in the exact frozen wire shapes, from real values.

    `config` is this side's opening candidate, in the same `NegotiatedConfigWire`
    the peer transport carries - the peer still has to converge on it.
    """
    identity = compose.identity_for(group_id, slot)
    declared = encode_declaration(identity.declaration)
    return json.dumps(
        {
            "declaration": declared.model_dump(mode="json", exclude_none=True),
            "profiles": encode_profiles(identity.profiles).model_dump(mode="json"),
            "config": encode_config(r7.CONFIG).model_dump(mode="json"),
            "first_sub_game": identity.first_sub_game,
        }
    )


def written_launch(directory: Path, group_id: str = GROUP_A, slot: str = "group_a") -> Path:
    """Write the launch document a subprocess can be started with."""
    path = directory / "launch.json"
    path.write_text(launch_document(group_id, slot), encoding="utf-8")
    return path
