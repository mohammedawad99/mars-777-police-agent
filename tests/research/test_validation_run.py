"""Evaluating a frozen candidate on a bank it has never been tuned on.

The properties that matter are structural, so they are proved on a handful of
scenarios rather than on the research corpus: the pairing refuses anything that
does not line up, the candidate's source hash is checked against the frozen one
before a game is played, and no code path can name a sealed set.
"""

import ast
import json
from pathlib import Path

import pytest
from research.records import write_csv
from research.validation import (
    BANKS,
    FROZEN_C4_SHA256,
    assess,
    evaluate,
    frozen_source_sha256,
)
from test_research_records import record

from research import validation

SOURCE = Path(validation.__file__)


def _bank(root: Path, name: str, count: int = 12) -> None:
    """Write a tiny bank under the filename the evaluator actually reads."""
    rows = tuple(
        record(
            scenario_id=f"{index:064d}",
            seed=index,
            seed_set="holdout" if name == "validation" else name,
            opponent_family="evasive" if index % 2 else "random_legal",
            outcome="CAPTURE" if index % 3 else "SURVIVAL",
        )
        for index in range(count)
    )
    write_csv(rows, root / "baseline" / BANKS[name])


def test_the_evaluator_knows_only_banks_that_are_not_sealed() -> None:
    assert set(BANKS) == {"validation", "stress"}
    assert "final_holdout" not in BANKS


def test_no_line_of_the_evaluator_names_a_sealed_set() -> None:
    """Checked on code, not prose: the docstrings legitimately say the word."""
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    holders = (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
    docs = {
        ast.get_docstring(node, clean=False) for node in ast.walk(tree) if isinstance(node, holders)
    }
    named = {
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    } - docs

    assert not any("final_holdout" in one or "final-holdout" in one for one in named)


def test_the_frozen_hash_is_the_one_the_development_evidence_was_produced_with() -> None:
    committed = Path("results/candidates/full_C4.json")
    if not committed.exists():
        pytest.skip("no committed development evidence in this working tree")
    published = json.loads(committed.read_text(encoding="utf-8"))["candidate_sha256"]

    assert FROZEN_C4_SHA256 == published == frozen_source_sha256()


def test_a_changed_candidate_is_refused_before_a_single_game_is_played() -> None:
    """If C4 fails, C4 fails; it must not be quietly re-frozen mid-stage."""
    with pytest.raises(ValueError, match="no longer matches"):
        evaluate(Path("results"), "validation", expect_sha256="0" * 64)


def test_an_evaluation_pairs_on_scenario_ids_and_writes_what_it_measured(
    tmp_path: Path,
) -> None:
    _bank(tmp_path, "validation")

    found = evaluate(tmp_path, "validation", expect_sha256=FROZEN_C4_SHA256)

    written = json.loads((tmp_path / "candidates" / "validation_C4.json").read_text("utf-8"))
    assert found["bank"] == "validation"
    assert found["overall"]["n"] == 12
    assert written["candidate_sha256"] == FROZEN_C4_SHA256
    assert "NOT FINAL HOLDOUT" in str(written["label"]).upper()
    assert (tmp_path / "candidates" / "validation_C4.csv").exists()


def test_the_assessment_reports_every_gate_rather_than_a_single_word() -> None:
    found = assess(
        overall={"n": 300, "delta": 0.06, "low": 0.04, "high": 0.08},
        families={"evasive": {"n": 40, "delta": -0.30, "low": -0.40, "high": -0.20}},
        configs={},
        latency_ok=True,
        legality_failures=0,
        sha_unchanged=True,
    )

    assert found["gates"]["C_positive_delta"] is True
    assert found["gates"]["E_no_material_family_regression"] is False
    assert found["passed"] is False
    assert "evasive" in found["material_regressions"]


def test_an_assessment_passes_only_when_every_gate_passes() -> None:
    clean = assess(
        overall={"n": 300, "delta": 0.06, "low": 0.04, "high": 0.08},
        families={"evasive": {"n": 40, "delta": 0.01, "low": -0.02, "high": 0.05}},
        configs={"grid7": {"n": 60, "delta": 0.02, "low": 0.001, "high": 0.05}},
        latency_ok=True,
        legality_failures=0,
        sha_unchanged=True,
    )

    assert clean["passed"] is True
    assert all(clean["gates"].values())
    assert clean["material_regressions"] == []


def test_a_legality_failure_fails_the_assessment_whatever_the_delta(tmp_path: Path) -> None:
    found = assess(
        overall={"n": 300, "delta": 0.20, "low": 0.15, "high": 0.25},
        families={},
        configs={},
        latency_ok=True,
        legality_failures=1,
        sha_unchanged=True,
    )

    assert found["gates"]["A_zero_legality_failures"] is False
    assert found["passed"] is False


def test_an_unknown_bank_is_refused_by_name(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="unknown bank"):
        evaluate(tmp_path, "invented", expect_sha256=FROZEN_C4_SHA256)


def test_a_measured_cell_reports_whether_it_is_a_material_regression() -> None:
    from research.gates import Cell

    found = Cell("random_legal", 317, -0.0063, -0.0189, 0.0347).as_record()

    assert found["group"] == "random_legal"
    assert found["material_regression"] is False
    assert found["ci_low"] == -0.0189
