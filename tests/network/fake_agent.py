"""A fake ngrok agent process: log lines in, termination recorded.

It imitates only what the real agent was **measured** to do - emit structured
JSON lines, one of which carries the Agent API address - so a production change
that stopped parsing those lines would still fail here.
"""

from dataclasses import dataclass, field

WEB_LINE = '{"lvl":"info","msg":"starting web service","obj":"web","addr":"127.0.0.1:4040"}'
SESSION_LINE = '{"lvl":"info","msg":"tunnel session started","obj":"tunnels.session"}'
NOISE_LINE = "not json at all"


class StubbornTimeoutError(Exception):
    """Stand-in for `subprocess.StubbornTimeoutError`, raised by a stubborn fake."""


@dataclass(slots=True)
class FakeStream:
    lines: list[str]

    def readline(self) -> str:
        return self.lines.pop(0) if self.lines else ""


@dataclass(slots=True)
class FakeAgent:
    """Enough of `subprocess.Popen` for the lifecycle under test."""

    lines: list[str] = field(default_factory=lambda: [SESSION_LINE, WEB_LINE])
    stubborn: bool = False
    alive: bool = True
    terminated: int = 0
    killed: int = 0
    waits: list[float] = field(default_factory=list)
    stdout: FakeStream | None = None

    def __post_init__(self) -> None:
        self.stdout = FakeStream(list(self.lines))

    def poll(self) -> int | None:
        return None if self.alive else 0

    def terminate(self) -> None:
        self.terminated += 1
        if not self.stubborn:
            self.alive = False

    def kill(self) -> None:
        self.killed += 1
        self.alive = False

    def wait(self, timeout: float) -> int:
        self.waits.append(timeout)
        if self.stubborn and self.killed == 0:
            raise StubbornTimeoutError
        return 0
