"""The one-shot execution path, exercised on a synthetic sealed set.

Split from `test_final_holdout_runner.py`, which proves the refusals. The set
built here is two seeds of one family on one board, invented for the test - the
real sealed set is never enumerated, played or read.
"""

from pathlib import Path

import pytest
from research.final_evaluation import RESULT_NAME, AlreadyConsumedError

FAKE_COMMITMENT = "a" * 64


def _seal(root: Path, **overrides: object) -> Path:
    import json

    document = {
        "bank": "final_holdout",
        "commitment_sha256": FAKE_COMMITMENT,
        "count": 11,
        "results_present": False,
        **overrides,
    }
    root.mkdir(parents=True, exist_ok=True)
    path = root / "final_holdout.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    return path


def _tiny_sealed(monkeypatch: pytest.MonkeyPatch) -> str:
    """A synthetic sealed set: two seeds, one family, one config. Never the real one."""
    from research.configs import corpus
    from research.scenario import openings, scenario_id
    from research.sealed import SealedSet

    from research import final_evaluation, seeds

    small = corpus()[0]
    bank = seeds.SeedBank("fake_sealed", (11, 12))
    monkeypatch.setattr(final_evaluation, "_FAMILIES", ("evasive",), raising=False)

    def fake_sealed(role: str) -> SealedSet:
        found = [
            scenario_id(role, "evasive", small, seed, police, thief)
            for seed, police, thief in openings(small, bank.seeds)
        ]
        return SealedSet(role, tuple(found))

    monkeypatch.setattr("research.sealed.sealed_set", fake_sealed)
    monkeypatch.setattr("research.seeds.final_holdout_bank", lambda: bank)
    monkeypatch.setattr("research.opponents.FAMILIES", ("evasive",))
    monkeypatch.setattr("research.runner.FAMILIES", ("evasive",))
    monkeypatch.setattr("research.runner.corpus", lambda: (small,))
    return fake_sealed("police").commitment


def test_the_runner_plays_both_sides_and_publishes_once(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The whole one-shot path on a synthetic seal, then refusing a repeat."""
    from research.candidates.registry import CANDIDATES

    from research import final_evaluation

    commitment = _tiny_sealed(monkeypatch)
    _seal(tmp_path, commitment_sha256=commitment)
    candidate = CANDIDATES["C4"].source_sha256

    found = final_evaluation.run_once(tmp_path, commitment, candidate)

    assert found["overall"]["n"] > 0
    assert found["candidate_sha256"] == candidate
    assert found["legality_failures"] == 0
    assert set(found["family"]) == {"evasive"}
    assert (tmp_path / "candidates" / RESULT_NAME).exists()

    with pytest.raises(AlreadyConsumedError):
        final_evaluation.run_once(tmp_path, commitment, candidate)


def test_the_confirmed_entry_point_runs_and_reports(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from research import final_main

    monkeypatch.setattr(final_main, "run_once", lambda root, one, two: {"path": str(root)})

    assert final_main.main([final_main.CONFIRM, "--out", str(tmp_path)]) == 0


def test_the_one_shot_command_is_runnable_as_a_module(tmp_path: Path) -> None:
    """`python -m research.final_main` is the documented entry, and it refuses.

    Run without the confirmation flag on an empty directory: the child must exit
    non-zero having played nothing, which exercises the module entry without
    going anywhere near the sealed set.
    """
    import os
    import subprocess
    import sys

    root = Path(__file__).resolve().parents[2]

    finished = subprocess.run(
        [sys.executable, "-m", "research.final_main", "--out", str(tmp_path)],
        capture_output=True,
        text=True,
        check=False,
        cwd=root,
        env={**os.environ, "PYTHONPATH": str(root)},
    )

    assert finished.returncode != 0
    assert "refusing" in finished.stderr
    assert not (tmp_path / "candidates" / RESULT_NAME).exists()
