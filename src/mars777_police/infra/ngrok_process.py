"""Starting, watching and reliably stopping the external ngrok Agent.

The agent is an **external executable**, not a library: no SDK is imported and
no dependency is added. It is spawned with an argument list - never a shell -
so nothing in a path can be interpreted, and `FR-051` is respected because no
credential is ever an argument.

Its Agent API address is not settable by any 3.39.10 command-line flag (the
option list was enumerated to confirm that), so it is read from the agent's own
**structured JSON log**: the event whose `obj` is `"web"` carries `addr`. That
is parsed JSON, not console text - a banner scrape would break the moment the
human-facing UI changed.

Termination is bounded and two-stage, and `stop` is idempotent, because the
alternative to a guaranteed stop is an orphaned tunnel still advertising a public
URL after the process that owned it has gone.
"""

import json
import subprocess
import time
from collections.abc import Callable
from dataclasses import dataclass, field

from ..app.public_ingress import PublicIngressError
from .ngrok_settings import NgrokSettings
from .provider_sanitize import sanitize

TERMINATE_SECONDS = 15.0
KILL_SECONDS = 10.0
Spawner = Callable[[tuple[str, ...]], "subprocess.Popen[str]"]


def spawn(argv: tuple[str, ...]) -> "subprocess.Popen[str]":
    """Start the agent with an argument list. No shell, ever."""
    return subprocess.Popen(
        list(argv),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )


@dataclass(slots=True)
class NgrokProcess:
    """One agent process and the Agent API address it reported."""

    settings: NgrokSettings
    spawner: Spawner = spawn
    monotonic: Callable[[], float] = time.monotonic
    process: "subprocess.Popen[str] | None" = field(default=None)
    api_base: str | None = field(default=None)

    def start(self, port: int) -> str:
        """Spawn the agent for *port* and return its Agent API base URL."""
        self.process = self.spawner(self.settings.argv(port))
        stream = self.process.stdout
        if stream is None:  # pragma: no cover - spawn always pipes stdout
            raise PublicIngressError("the agent was started without a readable stream")
        deadline = self.monotonic() + self.settings.startup_seconds
        while self.monotonic() < deadline:
            line = stream.readline()
            if not line:
                break
            event = self._event(line)
            if event is None:
                continue
            if event.get("lvl") in {"eror", "crit"}:
                detail = sanitize(str(event.get("err") or event.get("msg") or ""))
                self.stop()
                raise PublicIngressError(f"the tunnel provider refused to start: {detail}")
            address = event.get("addr")
            if event.get("obj") == "web" and type(address) is str and address:
                self.api_base = f"http://{address}"
                return self.api_base
        self.stop()
        raise PublicIngressError("the agent did not report an Agent API address in time")

    @staticmethod
    def _event(line: str) -> dict[str, object] | None:
        try:
            parsed = json.loads(line)
        except json.JSONDecodeError:
            return None
        return parsed if isinstance(parsed, dict) else None

    @property
    def is_running(self) -> bool:
        """Whether the agent process is still alive."""
        return self.process is not None and self.process.poll() is None

    def stop(self) -> None:
        """Terminate the agent, escalating to a kill. Safe to call repeatedly."""
        process, self.process, self.api_base = self.process, None, None
        if process is None:
            return
        process.terminate()
        try:
            process.wait(timeout=TERMINATE_SECONDS)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=KILL_SECONDS)
