"""The one-shot runner, exercised entirely on fake sealed metadata.

Nothing here reads, enumerates or plays the real sealed set: a test that opened
the holdout to prove the holdout is closed would consume the thing it protects.
Every fixture below is a synthetic seal with invented digests.
"""

import json
from pathlib import Path

import pytest
from research.final_evaluation import (
    RESULT_NAME,
    AlreadyConsumedError,
    SealMismatchError,
    guard,
    publish,
)

FAKE_COMMITMENT = "a" * 64
FAKE_CANDIDATE = "b" * 64


def _seal(root: Path, **overrides: object) -> Path:
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


def test_a_matching_seal_and_candidate_are_admitted(tmp_path: Path) -> None:
    _seal(tmp_path)

    found = guard(tmp_path, FAKE_COMMITMENT, FAKE_CANDIDATE, FAKE_CANDIDATE)

    assert found["commitment_sha256"] == FAKE_COMMITMENT
    assert found["count"] == 11


def test_a_changed_commitment_stops_the_run(tmp_path: Path) -> None:
    """The set being judged must be the set that was sealed."""
    _seal(tmp_path, commitment_sha256="c" * 64)

    with pytest.raises(SealMismatchError, match="commitment"):
        guard(tmp_path, FAKE_COMMITMENT, FAKE_CANDIDATE, FAKE_CANDIDATE)


def test_a_seal_that_already_reports_results_stops_the_run(tmp_path: Path) -> None:
    _seal(tmp_path, results_present=True)

    with pytest.raises(SealMismatchError, match="results"):
        guard(tmp_path, FAKE_COMMITMENT, FAKE_CANDIDATE, FAKE_CANDIDATE)


def test_a_candidate_that_moved_since_the_freeze_stops_the_run(tmp_path: Path) -> None:
    """No tuned revision may be slipped into the one evaluation that counts."""
    _seal(tmp_path)

    with pytest.raises(SealMismatchError, match="candidate"):
        guard(tmp_path, FAKE_COMMITMENT, FAKE_CANDIDATE, "d" * 64)


def test_a_completed_evaluation_refuses_a_second_run(tmp_path: Path) -> None:
    """The holdout is consumed; a rerun to reduce variance is not permitted."""
    _seal(tmp_path)
    (tmp_path / "candidates").mkdir(parents=True, exist_ok=True)
    (tmp_path / "candidates" / RESULT_NAME).write_text(
        json.dumps({"commitment_sha256": FAKE_COMMITMENT, "candidate_sha256": FAKE_CANDIDATE}),
        encoding="utf-8",
    )

    with pytest.raises(AlreadyConsumedError, match="already"):
        guard(tmp_path, FAKE_COMMITMENT, FAKE_CANDIDATE, FAKE_CANDIDATE)


def test_publication_is_atomic_and_leaves_no_partial_file(tmp_path: Path) -> None:
    """A result is historical evidence; a half-written one must never appear."""
    written = publish(tmp_path, {"n": 11})

    assert written.name == RESULT_NAME
    assert json.loads(written.read_text(encoding="utf-8"))["n"] == 11
    assert list(written.parent.glob("*.tmp")) == []


def test_publication_refuses_to_overwrite_a_recorded_result(tmp_path: Path) -> None:
    publish(tmp_path, {"n": 11})

    with pytest.raises(AlreadyConsumedError):
        publish(tmp_path, {"n": 12})


def test_an_interrupted_setup_leaves_no_result_behind(tmp_path: Path) -> None:
    """A guard failure must not look like a completed evaluation afterwards."""
    _seal(tmp_path, commitment_sha256="c" * 64)

    with pytest.raises(SealMismatchError):
        guard(tmp_path, FAKE_COMMITMENT, FAKE_CANDIDATE, FAKE_CANDIDATE)

    assert not (tmp_path / "candidates" / RESULT_NAME).exists()


def test_the_runner_refuses_when_the_enumeration_does_not_reproduce_the_seal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The scenarios judged must be the scenarios committed, recomputed now."""
    from research import final_evaluation

    _seal(tmp_path)
    monkeypatch.setattr(
        final_evaluation, "guard", lambda *args: {"commitment_sha256": FAKE_COMMITMENT}
    )

    with pytest.raises(SealMismatchError, match="reproduce"):
        final_evaluation.run_once(tmp_path, FAKE_COMMITMENT, FAKE_CANDIDATE)


def test_the_final_evaluation_needs_an_explicit_confirmation(tmp_path: Path) -> None:
    """No default, no `all`, no habit can spend the sealed set."""
    from research import final_main

    with pytest.raises(SystemExit, match="refusing"):
        final_main.main(["--out", str(tmp_path)])

    assert not (tmp_path / "candidates" / RESULT_NAME).exists()


def test_the_ordinary_research_commands_cannot_reach_the_final_evaluation() -> None:
    from research import candidate_main, final_main

    assert "final" not in candidate_main.parse_args(["screen"]).action
    for action in ("screen", "full", "latency", "belief", "figures", "evidence", "freeze"):
        assert candidate_main.parse_args([action]).action == action
    with pytest.raises(SystemExit):
        candidate_main.parse_args(["final"])
    assert final_main.COMMITMENT.startswith("99bd72e1")
