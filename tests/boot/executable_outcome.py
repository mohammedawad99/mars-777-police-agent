"""How a real process ended, judged from outside it.

A finished run is an exit status, two streams and a duration, and the questions
worth asking of it are narrow: did it stop cleanly, did it crash, which status
wins when two processes disagree, and did the one we are waiting for reach the
point we are waiting for. Nothing here starts anything.
"""

import http.client
import subprocess
import time
from collections.abc import Sequence
from dataclasses import dataclass

from boot_builders import HOST
from executable_process import (
    CONNECTION_REPORT,
    FAILURE,
    KILL_SECONDS,
    MCP_PATH,
    POLL_SECONDS,
    READY_TIMEOUT,
    SUB_GAME_IN_NAME,
)


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


def highest(names: Sequence[str], family: str) -> str:
    """The furthest `gNN` *family* reached, or `none` if it never started."""
    tokens = [
        found.group(1)
        for name in names
        if name.startswith(family) and (found := SUB_GAME_IN_NAME.search(name))
    ]
    return max(tokens) if tokens else "none"


def crashed(err: str) -> bool:
    """True when *err* names an exception that is not a connection report."""
    for line in err.splitlines():
        found = FAILURE.match(line)
        if found and not any(known in line for known in CONNECTION_REPORT):
            return True
    return False


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
