"""Running the candidate actions, and what each one must write.

Split from `test_candidate_cli.py`, which proves the command line has no door to
a held-out set; this file proves the doors it does have actually work.
"""

import json
from pathlib import Path

import pytest
from research.candidate_main import CEILING_MS, TIMED, latency
from research.records import write_csv
from test_research_records import record

from research import candidate_main


def _screening() -> dict[str, object]:
    """The smallest screening document the figure stage will accept."""
    cell = {
        "revision": "r1",
        "summary": "s",
        "overall": {"n": 9, "baseline_wins": 1, "candidate_wins": 2, "gains": 1, "losses": 0},
        "paired_ci": {"mean": 0.1, "ci_low": 0.0, "ci_high": 0.2},
    }
    return {"screening": {"n": 9}, "C1": cell, "C2": cell, "C3": cell, "C4": cell}


def _result() -> dict[str, object]:
    """The smallest evaluation document the evidence figures will accept."""
    cell = {"n": 9, "delta": 0.06, "ci_low": 0.04, "ci_high": 0.08}
    return {
        "overall": dict(cell),
        "family": {"evasive": dict(cell), "random_legal": {**cell, "delta": -0.01}},
        "config": {"grid7": dict(cell)},
    }


def _development(root: Path, count: int) -> None:
    rows = tuple(
        record(
            scenario_id=f"{index:064d}",
            seed=index,
            outcome="CAPTURE" if index % 2 else "SURVIVAL",
        )
        for index in range(count)
    )
    write_csv(rows, root / "baseline" / "games_development.csv")


def test_latency_is_measured_on_the_board_the_baseline_used_and_on_the_largest(
    tmp_path: Path,
) -> None:
    """A ceiling that only holds on the smallest legal board holds nothing."""
    from research.configs import corpus

    timed = [corpus()[index] for index in TIMED]

    assert [one.name for one in timed] == ["grid9", "grid11"]
    assert max(one.grid for one in timed) == max(one.grid for one in corpus())


def test_every_measured_candidate_is_judged_against_the_frozen_ceiling() -> None:
    """Asserted on the committed artifact rather than by re-timing eight cases.

    Re-measuring four candidates on two boards costs minutes, and it would cost
    them on every CI run of both operating systems. The measurement itself is
    a committed research artifact; what a test must protect is that the recorded
    numbers are inside the ceiling and that the ceiling has not drifted.
    """
    path = Path(__file__).resolve().parents[2] / "results" / "candidates" / "latency.json"
    if not path.exists():
        pytest.skip("no committed latency record in this working tree")
    found = json.loads(path.read_text(encoding="utf-8"))

    assert found["ceiling_ms"] == CEILING_MS == 25.0
    for name in ("grid9", "grid11"):
        for key in ("C1", "C2", "C3", "C4"):
            assert found[name][key]["within_ceiling"] is True
            assert found[name][key]["p95_ms"] <= CEILING_MS


def test_the_latency_action_writes_a_judged_record(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """One live measurement, smallest board, few samples: this proves the *path*.

    Whether the shipped policy is fast enough is a research measurement with its
    own committed artifact and its own assertion above. Re-deriving a stable p95
    here would buy nothing and cost seconds on every CI run of both operating
    systems.
    """
    from research import candidate_main as module
    from research import latency as timing

    monkeypatch.setattr(timing, "SAMPLE_TARGET", 12)
    monkeypatch.setattr(module, "TIMED", (0,))
    found = latency(tmp_path)
    written = json.loads((tmp_path / "candidates" / "latency.json").read_text(encoding="utf-8"))

    assert found["ceiling_ms"] == CEILING_MS
    assert written["grid7"]["C4"]["within_ceiling"] is True


def test_the_main_entry_runs_each_action(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Every action routes and writes its artifact.

    That is a routing property, so it is proved on the smallest bank that still
    exercises each path rather than on a benchmark-sized one.
    """
    from research import diagnostics
    from research import latency as timing

    _development(tmp_path, 16)
    monkeypatch.setattr(timing, "SAMPLE_TARGET", 12)
    monkeypatch.setattr(candidate_main, "TIMED", (0,))
    monkeypatch.setattr(diagnostics, "SAMPLED", range(50, 52))

    for argv in (
        ["screen"],
        ["full", "--candidate", "C4"],
        ["belief"],
        ["latency"],
        ["figures"],
    ):
        assert candidate_main.main([*argv, "--out", str(tmp_path)]) == 0

    assert (tmp_path / "figures" / "candidates" / "candidate_delta.png").exists()
    assert (tmp_path / "candidates" / "belief.json").exists()


def test_the_evidence_figures_are_their_own_action(tmp_path: Path) -> None:
    """Drawn from the validation and stress documents, not from screening.

    Kept a separate command rather than folded into `figures`, because a
    regeneration step that silently skipped a missing result file would look
    identical to one that drew it.
    """
    candidates = tmp_path / "candidates"
    candidates.mkdir(parents=True)
    (candidates / "screening.json").write_text(json.dumps(_screening()), encoding="utf-8")
    for name in ("full", "validation", "stress"):
        (candidates / f"{name}_C4.json").write_text(json.dumps(_result()), encoding="utf-8")

    assert candidate_main.main(["evidence", "--out", str(tmp_path)]) == 0

    drawn = sorted(one.name for one in (tmp_path / "figures" / "candidates").glob("*.png"))
    assert drawn == [
        "c4_by_bank.png",
        "c4_stress_family.png",
        "c4_validation_family.png",
        "strategy_research_progression.png",
    ]


def test_the_evidence_action_refuses_when_a_result_is_missing(tmp_path: Path) -> None:
    candidates = tmp_path / "candidates"
    candidates.mkdir(parents=True)
    (candidates / "screening.json").write_text(json.dumps(_screening()), encoding="utf-8")

    with pytest.raises(FileNotFoundError):
        candidate_main.main(["evidence", "--out", str(tmp_path)])


def test_the_candidate_command_is_runnable_as_a_module(tmp_path: Path) -> None:
    """`uv run python -m research.candidate_main` really is the documented entry.

    Only the figure stage is run in the child: replaying a bank in a subprocess
    would turn a unit suite into a benchmark, and every action is exercised
    in-process above.
    """
    import os
    import subprocess
    import sys

    source = tmp_path / "candidates" / "screening.json"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text(json.dumps(_screening()), encoding="utf-8")
    root = Path(__file__).resolve().parents[2]

    finished = subprocess.run(
        [sys.executable, "-m", "research.candidate_main", "figures", "--out", str(tmp_path)],
        capture_output=True,
        text=True,
        check=False,
        cwd=root,
        env={**os.environ, "PYTHONPATH": str(root)},
    )

    assert finished.returncode == 0, finished.stderr
    assert (tmp_path / "tables" / "candidates" / "screening.csv").exists()
