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
import threading
import time
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

import composed_builders as compose
import process_trace
import r7_builders as r7
import stack_attach
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


EXPERIMENTAL_LOOP = "selector"
"""The one variable of the R12 experiment: the **synthetic opponent's** loop.

The shipped CLI is untouched and keeps its default Windows loop, because the
thirty-second scheduling stall was measured in the opponent's process. Naming
it here keeps the experiment in test infrastructure and out of any shipped
setting, launch input or negotiated config.
"""


BOOTSTRAP = Path(__file__).with_name("client_bootstrap")
"""Where the test-only `sitecustomize` that times the CLI's HTTP writes lives."""


def measured(environ: dict[str, str], trace: Path | None) -> dict[str, str]:
    """Ask the spawned CLI to time its own HTTP writes, without touching `src`.

    The interpreter imports `sitecustomize` at startup, so putting one on the
    child's `PYTHONPATH` is how a measurement reaches a shipped entrypoint from
    outside it. Absent the trace variable the module does nothing at all.
    """
    if trace is None:
        return environ
    existing = os.environ.get("PYTHONPATH", "")
    joined = os.pathsep.join([str(BOOTSTRAP), existing]) if existing else str(BOOTSTRAP)
    return {**environ, "PYTHONPATH": joined, "MARS777_CLIENT_TRACE": str(trace)}


def spawn(
    package: str, launch: Path, environ: dict[str, str], trace: Path | None = None
) -> "subprocess.Popen[str]":
    """Start the real executable, in its own process group where that is needed."""
    return subprocess.Popen(
        [sys.executable, "-m", package, "--launch", str(launch)],
        env={**os.environ, **measured(environ, trace)},
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        creationflags=GROUP_FLAG,
    )


def spawn_opponent(
    role: str,
    port: int,
    opponent_url: str,
    root: Path,
    variant: str = "same",
    trace: Path | None = None,
    loop: str = "",
) -> "subprocess.Popen[str]":
    """Start the **synthetic, non-counted** distinct-group opponent process.

    A separate OS process with its own memory, its own artifact root and its own
    `SeriesDriver`. It is not a league participant and its result is not match
    evidence; it exists so the shipped CLI has a lawful counterparty to boot
    against without weakening anti-self-play.
    """
    script = Path(__file__).with_name("opponent_entrypoint.py")
    arguments = [role, str(port), opponent_url, str(root), variant]
    if trace is not None:
        arguments.append(str(trace))
    chosen = {"MARS777_TEST_EVENT_LOOP": loop} if loop else {}
    return subprocess.Popen(
        [sys.executable, str(script), *arguments],
        env={**os.environ, **chosen},
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        creationflags=GROUP_FLAG,
    )


def official(root: Path) -> list[str]:
    """The official file names a finished side left behind, sorted."""
    return sorted(path.name for path in root.iterdir()) if root.exists() else []


KILL_SECONDS = 10.0
"""How long a killed process is given to hand over what it had already written."""


@dataclass(frozen=True)
class Ran:
    """One finished process, kept whole so a failure can describe **both** sides.

    A two-process run that stalls is a statement about a pair, not about one
    process: asserting the first side's status before the second was ever
    collected reported one stack and silently discarded the peer holding the
    other end of it.
    """

    name: str
    pid: int
    status: int | None
    out: str
    err: str
    timed_out: bool = False


def finished(name: str, child: "subprocess.Popen[str]", timeout: float) -> Ran:
    """Collect a process whole, bounded by *timeout* and never waiting past it.

    A peer that hangs is killed and still described. Letting `TimeoutExpired`
    escape would throw the evidence away in order to report the waiting, which
    is the one thing already known.
    """
    timed_out = False
    try:
        out, err = child.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        timed_out = True
        child.kill()
        out, err = child.communicate(timeout=KILL_SECONDS)
    return Ran(name, child.pid, child.returncode, out, err, timed_out)


SUB_GAME_IN_NAME = re.compile(r"_(g\d{2})\.")
"""The `gNN` an official per-sub-game file carries in its own name."""


def highest(names: Sequence[str], family: str) -> str:
    """The furthest `gNN` *family* reached, or `none` if it never started."""
    tokens = [
        found.group(1)
        for name in names
        if name.startswith(family) and (found := SUB_GAME_IN_NAME.search(name))
    ]
    return max(tokens) if tokens else "none"


def _log_lines(root: Path, names: Sequence[str]) -> list[str]:
    """What each **finalized** sub-game log already records, and nothing more."""
    lines = []
    for name in sorted(name for name in names if name.startswith("log_")):
        try:
            document = json.loads((root / name).read_text(encoding="utf-8"))
        except (OSError, ValueError) as failure:
            lines.append(f"    {name}: unreadable ({type(failure).__name__})")
            continue
        audit = document.get("audit", {})
        lines.append(
            f"    {name}: sub_game={document.get('sub_game')}"
            f" entries={len(document.get('entries', []))}"
            f" result={audit.get('result')}"
            f" semantic={audit.get('semantic', {}).get('verdict')}"
        )
    return lines


def snapshot(name: str, root: Path) -> str:
    """One side's persisted evidence: how far it got, read from files alone.

    A sub-game's config is written when it locks and its log only when it
    finishes, so `config g06` beside `log g05` places a stall inside g06 without
    any live progress record existing. The **step** inside the active round is
    not persisted until that sub-game finalizes, so it stays unknown here rather
    than being guessed at.
    """
    names = official(root)
    declared = any(one.startswith("declaration_") for one in names)
    concluded = any(one.startswith("result_") for one in names)
    lines = [
        f"  {name} artifacts in {root}: {len(names)} file(s)",
        f"    declaration: {'yes' if declared else 'no'}",
        f"    result: {'yes' if concluded else 'no'}",
        f"    highest locked config: {highest(names, 'config_')}",
        f"    highest completed log: {highest(names, 'log_')}",
        f"    names: {names}",
    ]
    return "\n".join([*lines, *_log_lines(root, names)])


ATTACH = "MARS777_STACK_ATTACH"
"""Opt-in for the external stack reader; off unless a checkpoint asks for it.

py-spy could not read the Windows target, so leaving the observer armed would
spend attach attempts on every run for nothing. The code stays; the attempts
do not happen unless this is set.
"""


def watch_stacks(pid: int, trace: Path) -> "stack_attach.Observer":
    """Start the parent-side stack observer for *pid*, in a daemon thread.

    It runs beside the test rather than inside the agent: the observed process
    gains no import, no timer and no task, which is the whole point after an
    in-process watchdog perturbed a green run.
    """
    observer = stack_attach.Observer(pid=pid, trace=trace)
    if os.environ.get(ATTACH) == "1":
        threading.Thread(target=observer.run, name="stack-observer", daemon=True).start()
    return observer


def two_process_report(
    runs: Sequence[Ran],
    roots: Sequence[tuple[str, Path]],
    trace: Path | None = None,
    client: Path | None = None,
    stacks: Sequence["stack_attach.Attempt"] = (),
) -> str:
    """Everything a failing two-process run knows, with the secret scrubbed.

    The scrub is belt and braces: the streams are separately asserted free of
    the synthetic secret, and this is the text a CI log would publish.
    """
    blocks = ["TWO-PROCESS DIAGNOSTIC"]
    for ran in runs:
        killed = " (killed after timeout)" if ran.timed_out else ""
        blocks.append(f"  {ran.name}: pid={ran.pid} exit={ran.status}{killed}")
    blocks.extend(snapshot(name, root) for name, root in roots)
    if trace is not None:
        blocks.append(process_trace.summary(trace))
    if client is not None:
        blocks.append(process_trace.client_report(client))
    if stacks:
        blocks.append(stack_attach.attach_report(stacks, _scrubbed))
    sse = [ran.name for ran in runs if "standalone SSE writer" in ran.err]
    accept = [ran.name for ran in runs if "IocpProactor.accept" in ran.err]
    blocks.append(f"  SSE writer error reported by: {sse or 'neither'}")
    blocks.append(f"  accept-task WinError 995 reported by: {accept or 'neither'}")
    for ran in runs:
        blocks.append(f"--- {ran.name} stdout ---\n{ran.out}")
        blocks.append(f"--- {ran.name} stderr ---\n{ran.err}")
    return _scrubbed("\n".join(blocks))


def _scrubbed(text: str) -> str:
    """The one scrubber every published diagnostic passes through."""
    return text.replace(SECRET, "<secret redacted>")


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


def launch_document(group_id: str = GROUP_A, slot: str = "group_a", config: object = None) -> str:
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
            "config": encode_config(config or r7.CONFIG).model_dump(mode="json"),
            "first_sub_game": identity.first_sub_game,
        }
    )


def written_launch(
    directory: Path, group_id: str = GROUP_A, slot: str = "group_a", config: object = None
) -> Path:
    """Write the launch document a subprocess can be started with."""
    path = directory / "launch.json"
    path.write_text(launch_document(group_id, slot, config), encoding="utf-8")
    return path
