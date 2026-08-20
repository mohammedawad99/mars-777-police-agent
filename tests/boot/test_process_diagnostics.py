"""The two-process failure harness itself, tested where it used to lose evidence.

Two identical Windows exact-SHA runs stalled mid-series and reported one stack
between them: the real CLI's. The opponent's exit code, streams and artifacts
were collected into locals the first failing assertion never reached, and the
runner's temp directory then took the artifact roots with it.

Nothing here judges the game. These are tests of the diagnostic itself - that a
failure describes **both** processes, that a hung side is killed rather than
waited on forever, that the persisted artifacts are read back correctly enough
to place a stall in a sub-game, and that the synthetic secret never survives
into the text a CI log would publish.
"""

import json
import subprocess
from pathlib import Path

import executable_evidence as evidence
import executable_outcome as outcome
from boot_builders import SECRET

REAL = "real CLI"
PEER = "synthetic opponent"


class FakeProcess:
    """A `Popen` stand-in: the harness only ever asks it these four things."""

    def __init__(
        self, pid: int, status: int, out: str = "", err: str = "", hangs: bool = False
    ) -> None:
        self.pid, self.returncode, self._out, self._err = pid, status, out, err
        self._hangs, self.killed, self.calls = hangs, False, 0

    def communicate(self, timeout: float | None = None) -> tuple[str, str]:
        self.calls += 1
        if self._hangs and not self.killed:
            raise subprocess.TimeoutExpired(cmd="fake", timeout=timeout or 0.0)
        return self._out, self._err

    def kill(self) -> None:
        self.killed = True

    def poll(self) -> int | None:
        return self.returncode


def test_a_finished_process_is_described_whole() -> None:
    child = FakeProcess(4242, 4, out="series stdout", err="the fatal stack")
    ran = outcome.finished(REAL, child, timeout=1.0)

    assert (ran.name, ran.pid, ran.status) == (REAL, 4242, 4)
    assert (ran.out, ran.err) == ("series stdout", "the fatal stack")
    assert not ran.timed_out and not child.killed


def test_a_hanging_process_is_killed_and_still_described() -> None:
    """The evidence is the point; `TimeoutExpired` escaping would discard it."""
    child = FakeProcess(7, 0, out="partial", err="held open", hangs=True)
    ran = outcome.finished(PEER, child, timeout=0.01)

    assert ran.timed_out and child.killed
    assert (ran.out, ran.err) == ("partial", "held open")
    assert child.calls == 2


def test_a_failing_side_does_not_hide_the_other(tmp_path: Path) -> None:
    """Either order: whichever process failed, both records reach the report."""
    ours = outcome.finished(REAL, FakeProcess(11, 4, "ours out", "ours stack"), timeout=1.0)
    theirs = outcome.finished(PEER, FakeProcess(22, 1, "theirs out", "theirs stack"), timeout=1.0)
    report = evidence.two_process_report(
        (ours, theirs), ((REAL, tmp_path / "a"), (PEER, tmp_path / "b"))
    )

    for expected in (
        "pid=11 exit=4",
        "pid=22 exit=1",
        "ours out",
        "ours stack",
        "theirs out",
        "theirs stack",
    ):
        assert expected in report, report


def test_the_report_names_a_killed_survivor(tmp_path: Path) -> None:
    hung = outcome.finished(PEER, FakeProcess(9, 0, hangs=True), timeout=0.01)
    report = evidence.two_process_report((hung,), ((PEER, tmp_path),))

    assert "killed after timeout" in report


def _write(root: Path, name: str, document: object) -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / name).write_text(json.dumps(document), encoding="utf-8")


def _log(sub_game: int, verdict: str = "CONSISTENT") -> dict[str, object]:
    return {
        "sub_game": sub_game,
        "entries": [{"step": 1}, {"step": 2}],
        "audit": {"result": "POLICE_WIN", "semantic": {"verdict": verdict}},
    }


def test_the_snapshot_places_a_stall_between_the_last_config_and_the_last_log(
    tmp_path: Path,
) -> None:
    """`config g06` beside `log g05` is what proves the stall happened in g06."""
    root = tmp_path / "mars777"
    _write(root, "declaration_G1.json", {"game_id": "G1"})
    for index in (1, 2, 3, 4, 5, 6):
        _write(root, f"config_G1_g0{index}.json", {"sub_game": index})
    for index in (1, 2, 3, 4, 5):
        _write(root, f"log_G1_g0{index}.json", _log(index))

    text = evidence.snapshot(REAL, root)

    assert "highest locked config: g06" in text
    assert "highest completed log: g05" in text
    assert "declaration: yes" in text
    assert "result: no" in text
    assert "sub_game=5 entries=2 result=POLICE_WIN semantic=CONSISTENT" in text


def test_the_snapshot_reports_a_side_that_wrote_nothing(tmp_path: Path) -> None:
    text = evidence.snapshot(PEER, tmp_path / "never-created")

    assert "0 file(s)" in text
    assert "highest locked config: none" in text
    assert "highest completed log: none" in text
    assert "declaration: no" in text


def test_the_snapshot_survives_an_unreadable_log(tmp_path: Path) -> None:
    """A truncated file is itself evidence; it must not end the diagnostic."""
    root = tmp_path / "mars777"
    root.mkdir()
    (root / "log_G1_g01.json").write_text("{not json", encoding="utf-8")

    assert "unreadable (JSONDecodeError)" in evidence.snapshot(REAL, root)


def test_a_completed_series_reports_its_result_file(tmp_path: Path) -> None:
    root = tmp_path / "mars777"
    _write(root, "result_G1.json", {"mutual_agreement": True})

    text = evidence.snapshot(REAL, root)
    assert "result: yes" in text
    assert "highest completed log: none" in text


def test_the_highest_token_ignores_a_family_it_was_not_asked_about() -> None:
    names = ["config_G1_g01.json", "config_G1_g02.json", "log_G1_g01.json"]

    assert outcome.highest(names, "config_") == "g02"
    assert outcome.highest(names, "log_") == "g01"
    assert outcome.highest(names, "result_") == "none"


def test_the_secret_never_reaches_the_published_report(tmp_path: Path) -> None:
    """The streams are asserted clean separately; this is the second line."""
    leaky = outcome.finished(REAL, FakeProcess(1, 1, f"out {SECRET}", f"err {SECRET}"), timeout=1.0)
    report = evidence.two_process_report((leaky,), ((REAL, tmp_path),))

    assert SECRET not in report
    assert report.count("<secret redacted>") == 2
