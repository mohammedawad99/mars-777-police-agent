"""Reading the opponent's thread stacks from **outside** the opponent process.

The previous attempt armed a repeating `faulthandler` timer inside the process
under study, and it broke a green Linux run: the loop stayed healthy, no send
stalled, and the peer simply stopped being served. An instrument that changes
the thing it measures cannot answer a question about that thing, so nothing
here runs in the target at all. The observed process is byte-for-byte the one
R13 already measured.

Instead the parent watches the trace the opponent is already writing, notices
that its heartbeat has fallen silent, and asks an external profiler to read
that process's stacks by pid. The target imports nothing, installs nothing and
is never asked to cooperate.

**The silence is the trigger, not the shape of the stall.** An earlier version
waited for a hand-off that had begun and not finished, which is one of the two
ways this defect presents; the run that followed presented the other, and the
observer never fired. The heartbeat stops in both.

**Never `--locals`.** Frame identity - file, function, line - is what the
question needs; the values inside those frames are protocol material and must
not reach a CI log.
"""

import json
import subprocess
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

TOOL = "py-spy"
VERSION = "0.4.1"
"""Pinned: a stack reader whose version drifts is a report whose shape drifts."""

STALE_SECONDS = 2.0
"""Four missed half-second beats: far outside jitter, far inside the blackout."""

HEALTHY_TICKS = 3
"""Proof the heartbeat was running before its silence can mean anything."""

OFFSETS = (0.0, 8.0, 18.0)
"""From detection, which is already ~2s in: roughly 2s, 10s and 20s of the gap.

Not +25s: that approaches the release boundary, and a third sample taken after
the loop resumes is worse than no third sample.
"""

POLL_SECONDS = 0.5


def command(pid: int) -> list[str]:
    """The exact invocation, with no local variables ever requested."""
    return [TOOL, "dump", "--pid", str(pid), "--nonblocking"]


@dataclass
class Attempt:
    """One external read, kept whether it succeeded or not.

    A profiler that could not attach is evidence about the diagnostic, not an
    absence of evidence, so a failure is recorded with its exit code and its
    complaint rather than dropped.
    """

    index: int
    pid: int
    at_ns: int
    offset: float
    status: int | None
    stdout: str
    stderr: str

    def failed(self) -> bool:
        return self.status != 0 or not self.stdout.strip()


@dataclass
class Observer:
    """Parent-side watcher: reads a trace, then reads stacks from outside.

    Everything it needs is injectable, so its behaviour can be proven without
    waiting real seconds or attaching to a real process.
    """

    pid: int
    trace: Path
    runner: Callable[[list[str]], subprocess.CompletedProcess[str]] | None = None
    clock: Callable[[], float] = time.monotonic
    stamp: Callable[[], int] = time.monotonic_ns
    sleeper: Callable[[float], None] = time.sleep
    alive: Callable[[], bool] = lambda: True
    attempts: list[Attempt] = field(default_factory=list)
    stopped: bool = False
    seen: int = 0
    fresh: float = 0.0
    detected: int | None = None

    def ticks(self) -> list[int]:
        """Every heartbeat this process has recorded, read from its own trace."""
        return [
            int(one["monotonic_ns"])
            for one in _lines(self.trace)
            if one.get("event") == "heartbeat_tick" and one.get("monotonic_ns") is not None
        ]

    def blacked_out(self) -> bool:
        """True when a heartbeat that *was* beating has gone quiet.

        The trigger is the silence itself, not the shape of whatever the loop
        was doing when it stopped. Two runs showed the send entered before the
        blackout and one showed it entered after; keying on either would miss
        the other, while the silence is present in both.

        Two guards keep it honest: the heartbeat must have proved a cadence
        first, so a process that has not started beating is never mistaken for
        one that stopped; and staleness is measured against this process's own
        latest tick, not against a clock shared with the target.
        """
        beats = self.ticks()
        if len(beats) < HEALTHY_TICKS:
            self.seen = 0
            return False
        if len(beats) > self.seen:
            self.seen, self.fresh = len(beats), self.clock()
        return self.clock() - self.fresh >= STALE_SECONDS

    def run(self) -> None:
        """Wait for the heartbeat to fall silent, then read stacks from outside.

        A resumed heartbeat ends the capture immediately: it is more
        authoritative than any assumption about what the loop was doing, and a
        dump taken after the loop recovers answers a different question.
        """
        while not self.stopped and self.alive():
            if not self.blacked_out():
                self.sleeper(POLL_SECONDS)
                continue
            self.detected = self.stamp()
            began = self.clock()
            for index, offset in enumerate(OFFSETS, start=1):
                while not self.stopped and self.clock() - began < offset:
                    if not self.blacked_out() or not self.alive():
                        return
                    self.sleeper(POLL_SECONDS)
                if self.stopped or not self.alive() or not self.blacked_out():
                    return
                self.capture(index, offset)
            return

    def capture(self, index: int, offset: float) -> Attempt:
        """Read the target's stacks once, recording exactly what came back."""
        run = self.runner or _run
        try:
            done = run(command(self.pid))
            attempt = Attempt(
                index, self.pid, self.stamp(), offset, done.returncode, done.stdout, done.stderr
            )
        except Exception as failure:  # pragma: no cover - the tool is absent
            attempt = Attempt(index, self.pid, self.stamp(), offset, None, "", repr(failure))
        self.attempts.append(attempt)
        return attempt

    def stop(self) -> None:
        self.stopped = True

    def write(self, directory: Path) -> Path:
        """Persist the attempts beside the trace, never into an artifact root."""
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / "opponent_stacks.json"
        path.write_text(
            json.dumps([one.__dict__ for one in self.attempts], indent=1), encoding="utf-8"
        )
        return path


def _run(argv: list[str]) -> "subprocess.CompletedProcess[str]":
    return subprocess.run(argv, capture_output=True, text=True, timeout=60, check=False)


def _lines(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    found = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.strip():
            try:
                found.append(json.loads(line))
            except ValueError:
                continue
    return found


ASYNCIO_FRAMES = ("asyncio", "base_events.py", "windows_events.py", "selectors.py")
"""What identifies the thread running the loop, from its frames rather than its
position in a list."""


def loop_frames(stdout: str) -> list[str]:
    """The frames of the thread whose stack names the event loop.

    Identified by what it is executing, not by ordinal position: a thread that
    happens to be printed first is not thereby the loop.
    """
    best: list[str] = []
    for block in _threads(stdout):
        if any(marker in one for one in block for marker in ASYNCIO_FRAMES) and len(block) > len(
            best
        ):
            best = block
    return best


def _threads(stdout: str) -> list[list[str]]:
    blocks: list[list[str]] = []
    for line in stdout.splitlines():
        stripped = line.strip()
        if stripped.startswith("Thread "):
            blocks.append([])
        elif blocks and stripped:
            blocks[-1].append(stripped)
    return blocks


POLLING = ("windows_events.py", "selectors.py", "base_events.py", "proactor_events.py")


def attach_verdict(attempts: Sequence[Attempt]) -> str:
    """Name what the loop thread was doing, only from frames actually read."""
    usable = [one for one in attempts if not one.failed()]
    if len(usable) < 2:
        broken = [one for one in attempts if one.failed()]
        detail = broken[0].stderr.strip().splitlines()[:1] if broken else []
        return (
            f"HX - {len(usable)} usable dump(s) of {len(attempts)}"
            f"{'; ' + detail[0] if detail else ''}"
        )
    tops = []
    for one in usable:
        frames = loop_frames(one.stdout)
        if not frames:
            return "HX - the event-loop thread could not be identified in every dump"
        tops.append(frames[0])
    if len(set(tops)) > 1:
        return "H4 - the loop thread was at different frames in each dump; no stable blocker"
    top = tops[0]
    if any(marker in top for marker in POLLING):
        return f"H2 - the loop thread sat in its own wait: {top}"
    return f"H1 - the loop thread was in a synchronous call: {top}"


def attach_report(attempts: Sequence[Attempt], scrub: Callable[[str], str], keep: int = 16) -> str:
    """The stacks read from outside, with the verdict they actually support."""
    if not attempts:
        return "    external stacks: no attach attempted"
    lines = [f"    external stacks: {len(attempts)} attempt(s) via {TOOL} {VERSION}"]
    for one in attempts:
        lines.append(
            f"      dump_{one.index} at ~+{one.offset:.0f}s pid={one.pid}"
            f" exit={one.status}{' FAILED' if one.failed() else ''}"
        )
        if one.failed():
            lines.extend(f"        ! {scrub(row)}" for row in one.stderr.splitlines()[:4])
            continue
        for block in _threads(one.stdout):
            lines.append(f"        thread: {len(block)} frames")
            lines.extend(f"          {scrub(row)}" for row in block[:keep])
    lines.append(f"      ATTACH VERDICT: {attach_verdict(attempts)}")
    return "\n".join(lines)
