"""The sealed set stays sealed, proved without touching it.

Every assertion here works from metadata, module structure and guards. None of
them loads the sealed scenarios - a security test that opened the file to prove
the file is closed would destroy the blindness it was written to protect.
"""

import ast
import json
from pathlib import Path

import pytest
from research.seeds import FINAL_HOLDOUT, banks, working_banks

from research import bench_main, candidate_main, freeze, validation

ROOT = Path(__file__).resolve().parents[2]
SEAL = ROOT / "results" / "final_holdout.json"
COMMITMENT = "99bd72e102d8a31e0b0937813166d87afd13034f5e191d834002df9e13358f47"
CANDIDATE_SHA = "1cc0a20d40680874a337dd3f7f2e552924763e42f291066990cb0dc8385c2884"


def test_no_working_sweep_can_reach_the_sealed_bank() -> None:
    """`working_banks` is what a sweep iterates; the sealed one is not in it."""
    assert FINAL_HOLDOUT not in [one.name for one in working_banks()]
    assert FINAL_HOLDOUT in [one.name for one in banks()]


def test_no_evaluation_command_offers_the_sealed_bank() -> None:
    assert FINAL_HOLDOUT not in validation.BANKS
    for forbidden in ("final_holdout", "final-holdout", "holdout-final"):
        with pytest.raises(SystemExit):
            candidate_main.parse_args([forbidden])


def test_the_all_command_sweeps_only_the_working_banks() -> None:
    """`all` must never quietly mean "and the sealed one too"."""
    source = ast.parse(Path(bench_main.__file__).read_text(encoding="utf-8"))
    called = {
        node.func.id
        for node in ast.walk(source)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }

    assert "working_banks" in called
    assert "final_holdout_bank" not in called


def test_no_evaluation_module_can_name_a_sealed_data_file() -> None:
    """Narrowed to what could actually *load* the set.

    `freeze.py` legitimately writes the field names `final_holdout` and
    `final_holdout_evaluated` - that record is how the stage proves the set was
    not evaluated, so a guard that failed on it would forbid the evidence rather
    than the leak. What must not appear is a literal that names sealed scenario
    data: a result row file, a CSV, a bank name handed to a sweep.
    """
    holders = (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
    allowed = {"final_holdout.json", "final_holdout", "final_holdout_evaluated"}
    for module in (validation, candidate_main, freeze):
        tree = ast.parse(Path(module.__file__).read_text(encoding="utf-8"))
        docs = {
            ast.get_docstring(node, clean=False)
            for node in ast.walk(tree)
            if isinstance(node, holders)
        }
        literals = {
            node.value
            for node in ast.walk(tree)
            if isinstance(node, ast.Constant) and isinstance(node.value, str)
        } - docs
        leaked = [
            one
            for one in literals
            if "final_holdout" in one and (one not in allowed or one.endswith(".csv"))
        ]

        assert leaked == [], module.__name__


def test_the_seal_still_reports_no_results() -> None:
    """Metadata only: this file carries a commitment, never a scenario list."""
    if not SEAL.exists():
        pytest.skip("no committed seal in this working tree")
    document = json.loads(SEAL.read_text(encoding="utf-8"))

    assert document["results_present"] is False
    assert document["commitment_sha256"] == COMMITMENT
    assert document["count"] == 2226
    assert "scenarios" not in document


def test_exactly_one_final_holdout_result_exists_and_it_is_the_one_shot() -> None:
    """Updated at Stage 9B-2, when the set was legitimately spent.

    Before the evaluation this asserted that **no** result existed. The property
    that matters now is that there is exactly **one**, produced by the single
    official run - a second file would mean the holdout had been replayed.
    """
    produced = sorted(
        one.name
        for one in (ROOT / "results").rglob("*.json")
        if one.is_file() and "final_holdout" in one.name and one.name != "final_holdout.json"
    )
    rows = sorted(one.name for one in (ROOT / "results").rglob("*final_holdout*.csv"))

    assert produced == ["final_holdout_result.json"]
    assert rows == [], "the sealed set has no committed row dump; only its summary"


def test_the_freeze_still_records_the_state_it_was_frozen_in() -> None:
    """The freeze is history and is not rewritten by what happened afterwards.

    It was written before the evaluation and says so. The record of the
    evaluation lives in its own one-shot result file; editing the freeze to
    match later events would destroy the evidence that the candidate really was
    fixed beforehand.
    """
    path = ROOT / "results" / "candidates" / "freeze_C4.json"
    if not path.exists():
        pytest.skip("no committed freeze in this working tree")
    document = json.loads(path.read_text(encoding="utf-8"))

    assert document["final_holdout_evaluated"] is False
    assert document["production_promotion"] is False
    assert document["candidate_sha256"] == CANDIDATE_SHA
    assert document["final_holdout"]["results_present"] is False
