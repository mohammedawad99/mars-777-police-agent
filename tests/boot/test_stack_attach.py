"""The external stack observer: what it runs, when, and against whom.

The instrument this replaces was armed inside the process under study and
broke a green run. So the property that matters most here is negative - the
target gains nothing - and the rest is about not lying: a profiler that could
not attach must be reported as a failed attach, never as an absent stall.

Nothing here waits real seconds. The clock, the sleeper and the process runner
are all injected, because a diagnostic whose tests take half a minute stops
being run.
"""

import json
import subprocess
from pathlib import Path

import stack_attach
from boot_builders import SECRET


def _scrub(text: str) -> str:
    return text.replace(SECRET, "<secret redacted>")


def _trace(path: Path, *rows: dict[str, object]) -> Path:
    path.write_text("\n".join(json.dumps(one) for one in rows), encoding="utf-8")
    return path


def _enter(seq: int = 1) -> dict[str, object]:
    return {
        "event": "memory_send_enter",
        "layer": "stream",
        "seq": seq,
        "monotonic_ns": 0,
        "item_type": "SessionMessage",
        "waiting_receivers": 1,
        "capacity": 0,
    }


def _exit(seq: int = 2) -> dict[str, object]:
    return {"event": "memory_send_exit", "layer": "stream", "seq": seq, "monotonic_ns": 1}


class FakeRunner:
    """Stands in for the external profiler; records exactly how it was called."""

    def __init__(
        self, stdout: str = "Thread 1 (idle)\n  x (asyncio/base_events.py:1)", code: int = 0
    ) -> None:
        self.argv: list[list[str]] = []
        self.stdout, self.code = stdout, code

    def __call__(self, argv: list[str]) -> "subprocess.CompletedProcess[str]":
        self.argv.append(argv)
        return subprocess.CompletedProcess(argv, self.code, self.stdout, "")


class Clock:
    """A clock the test advances, so offsets are exercised without waiting."""

    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.now += seconds


def _observer(
    tmp_path: Path, runner: FakeRunner, clock: Clock, **extra: object
) -> stack_attach.Observer:
    return stack_attach.Observer(
        pid=4242,
        trace=tmp_path / "trace.jsonl",
        runner=runner,
        clock=clock,
        sleeper=clock.sleep,
        stamp=lambda: int(clock.now * 1e9),
        **extra,
    )


def test_the_command_never_asks_for_locals() -> None:
    """Frame identity is the question; the values in them are protocol material."""
    argv = stack_attach.command(77)

    assert argv[:4] == ["py-spy", "dump", "--pid", "77"]
    assert "--nonblocking" in argv
    assert "--locals" not in argv and "-l" not in argv


def test_a_stalled_handoff_is_read_from_the_trace_alone(tmp_path: Path) -> None:
    _trace(tmp_path / "trace.jsonl", _enter())
    observer = _observer(tmp_path, FakeRunner(), Clock())

    assert observer.outstanding() is True


def test_a_completed_handoff_is_not_outstanding(tmp_path: Path) -> None:
    _trace(tmp_path / "trace.jsonl", _enter(), _exit())
    observer = _observer(tmp_path, FakeRunner(), Clock())

    assert observer.outstanding() is False


def test_three_dumps_are_taken_across_the_stall(tmp_path: Path) -> None:
    _trace(tmp_path / "trace.jsonl", _enter())
    runner, clock = FakeRunner(), Clock()

    _observer(tmp_path, runner, clock).run()

    assert len(runner.argv) == 3
    assert all(one == stack_attach.command(4242) for one in runner.argv)


def test_a_handoff_that_finishes_promptly_is_never_dumped(tmp_path: Path) -> None:
    """Only a stall is interesting; a healthy turn must cost nothing."""
    path = tmp_path / "trace.jsonl"
    _trace(path, _enter())
    runner, clock = FakeRunner(), Clock()
    observer = _observer(tmp_path, runner, clock)
    original = observer.outstanding
    calls = {"n": 0}

    def outstanding() -> bool:
        calls["n"] += 1
        if calls["n"] > 2:
            _trace(path, _enter(), _exit())
        return original()

    observer.outstanding = outstanding  # type: ignore[method-assign]
    observer.run()

    assert runner.argv == []


def test_nothing_is_dumped_after_the_opponent_exits(tmp_path: Path) -> None:
    _trace(tmp_path / "trace.jsonl", _enter())
    runner, clock = FakeRunner(), Clock()

    _observer(tmp_path, runner, clock, alive=lambda: False).run()

    assert runner.argv == []


def test_stopping_ends_the_watch(tmp_path: Path) -> None:
    _trace(tmp_path / "trace.jsonl", _enter())
    runner, clock = FakeRunner(), Clock()
    observer = _observer(tmp_path, runner, clock)
    observer.stop()

    observer.run()

    assert runner.argv == []


def test_a_failed_attach_is_recorded_rather_than_hidden(tmp_path: Path) -> None:
    """A profiler that could not attach is evidence, not an absence of it."""
    _trace(tmp_path / "trace.jsonl", _enter())
    runner = FakeRunner(stdout="", code=1)
    clock = Clock()

    observer = _observer(tmp_path, runner, clock)
    observer.run()

    assert len(observer.attempts) == 3
    assert all(one.failed() for one in observer.attempts)
    assert stack_attach.attach_verdict(observer.attempts).startswith("HX")


def test_a_tool_that_cannot_be_launched_is_recorded(tmp_path: Path) -> None:
    _trace(tmp_path / "trace.jsonl", _enter())

    def explode(argv: list[str]) -> "subprocess.CompletedProcess[str]":
        raise FileNotFoundError("py-spy")

    observer = _observer(tmp_path, FakeRunner(), Clock())
    observer.runner = explode  # type: ignore[assignment]
    attempt = observer.capture(1, 5.0)

    assert attempt.status is None and "FileNotFoundError" in attempt.stderr
    assert attempt.failed()


def test_the_loop_thread_is_found_by_its_frames_not_its_position() -> None:
    stdout = (
        "Thread 111 (active)\n  serve (app/worker.py:3)\n"
        "Thread 222 (idle)\n  _poll (asyncio/windows_events.py:786)\n"
        "  _run_once (asyncio/base_events.py:1922)\n"
    )

    frames = stack_attach.loop_frames(stdout)

    assert frames and "windows_events.py" in frames[0]


def test_a_stable_polling_frame_is_the_loop_in_its_own_wait() -> None:
    stdout = "Thread 222 (idle)\n  _poll (asyncio/windows_events.py:786)\n"
    attempts = [stack_attach.Attempt(index, 1, 0, 5.0, 0, stdout, "") for index in (1, 2)]

    assert stack_attach.attach_verdict(attempts).startswith("H2")


def test_a_stable_non_polling_frame_is_a_synchronous_call() -> None:
    stdout = "Thread 222 (idle)\n  read (app/blocking.py:9)\n  run (asyncio/base_events.py:1)\n"
    attempts = [stack_attach.Attempt(index, 1, 0, 5.0, 0, stdout, "") for index in (1, 2)]

    assert stack_attach.attach_verdict(attempts).startswith("H1")


def test_changing_frames_are_reported_as_no_stable_blocker() -> None:
    one = "Thread 1 (idle)\n  first (app/one.py:1)\n  run (asyncio/base_events.py:9)\n"
    two = "Thread 1 (idle)\n  second (app/two.py:2)\n  run (asyncio/base_events.py:9)\n"
    attempts = [
        stack_attach.Attempt(1, 1, 0, 5.0, 0, one, ""),
        stack_attach.Attempt(2, 1, 0, 15.0, 0, two, ""),
    ]

    assert stack_attach.attach_verdict(attempts).startswith("H4")


def test_one_usable_dump_is_not_enough_to_classify() -> None:
    stdout = "Thread 1 (idle)\n  _poll (asyncio/windows_events.py:786)\n"
    attempts = [stack_attach.Attempt(1, 1, 0, 5.0, 0, stdout, "")]

    assert stack_attach.attach_verdict(attempts).startswith("HX")


def test_the_report_scrubs_before_publishing(tmp_path: Path) -> None:
    stdout = f"Thread 1 (idle)\n  run ({SECRET}/thing.py:1)\n"
    attempts = [stack_attach.Attempt(index, 1, 0, 5.0, 0, stdout, "") for index in (1, 2)]

    text = stack_attach.attach_report(attempts, _scrub)

    assert SECRET not in text
    assert "<secret redacted>" in text


def test_the_report_names_a_failed_attach_and_its_complaint() -> None:
    attempts = [stack_attach.Attempt(1, 9, 0, 5.0, 1, "", "Permission Denied: try elevated")]

    text = stack_attach.attach_report(attempts, _scrub)

    assert "FAILED" in text and "Permission Denied" in text
    assert "ATTACH VERDICT: HX" in text


def test_no_attach_reports_itself_rather_than_an_empty_finding() -> None:
    assert "no attach attempted" in stack_attach.attach_report([], _scrub)


def test_attempts_are_written_beside_the_trace_not_into_an_artifact_root(
    tmp_path: Path,
) -> None:
    """Official files are the game's; a diagnostic must never join them."""
    _trace(tmp_path / "trace.jsonl", _enter())
    observer = _observer(tmp_path, FakeRunner(), Clock())
    observer.run()

    written = observer.write(tmp_path / "diagnostics")

    assert written.parent.name == "diagnostics"
    assert json.loads(written.read_text(encoding="utf-8"))[0]["pid"] == 4242
