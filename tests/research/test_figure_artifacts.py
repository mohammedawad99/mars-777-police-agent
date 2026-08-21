"""What the committed figure and table artifacts must contain.

Split from `test_candidate_figures.py`, which asserts how a figure is *drawn*;
this file asserts what the regeneration commands actually write.
"""

import csv
import json
from collections import Counter
from pathlib import Path

from research.gates import ADVANCED, NOT_ADVANCED, REJECTED_GATE

from research import candidate_tables


def test_the_rows_carry_every_candidate_in_the_order_tried(tmp_path: Path) -> None:
    document = {
        "screening": {"n": 471},
        **{
            key: {
                "revision": "r1",
                "summary": key,
                "overall": {
                    "n": 471,
                    "baseline_wins": 23,
                    "candidate_wins": 1,
                    "gains": 1,
                    "losses": 1,
                },
                "paired_ci": {"mean": 0.01, "ci_low": 0.0, "ci_high": 0.02},
            }
            for key in candidate_tables.ORDER
        },
    }
    source = tmp_path / "screening.json"
    source.write_text(json.dumps(document), encoding="utf-8")

    written = candidate_tables.write_all(source, tmp_path)

    body = (tmp_path / "tables" / "candidates" / "screening.csv").read_text(encoding="utf-8")
    parsed = list(csv.DictReader(body.splitlines()))
    verdicts = Counter(one["verdict"] for one in parsed)
    assert [one.name for one in written] == [
        "screening.csv",
        "candidate_delta.png",
        "exploration_progression.png",
    ]
    assert [one["candidate"] for one in parsed] == list(candidate_tables.ORDER)
    assert verdicts[ADVANCED] == len(candidate_tables.SELECTED)
    assert verdicts[NOT_ADVANCED] == 1, "C2 measured positive; it was not rejected"
    assert verdicts[REJECTED_GATE] == 2, "C1 and C3 failed on their own evidence"


def test_the_committed_figures_carry_the_development_only_label() -> None:
    assert "NOT FINAL HOLDOUT" in candidate_tables.LABEL
    assert "NOT PRODUCTION PROMOTION" in candidate_tables.LABEL


def test_the_holdout_point_is_drawn_once_it_has_been_recorded(tmp_path: Path) -> None:
    """Read from the recorded one-shot result, never recomputed."""
    from research.evidence_figures import FINAL_NAME, write_all

    cell = {"n": 9, "delta": 0.07, "ci_low": 0.05, "ci_high": 0.09}
    result = {
        "overall": dict(cell),
        "family": {"evasive": dict(cell)},
        "config": {"grid7": dict(cell)},
    }
    candidates = tmp_path / "candidates"
    candidates.mkdir(parents=True)
    for name in ("full_C4.json", "validation_C4.json", "stress_C4.json", FINAL_NAME):
        (candidates / name).write_text(json.dumps(result), encoding="utf-8")
    (candidates / "screening.json").write_text(json.dumps(_screening()), encoding="utf-8")

    written = sorted(one.name for one in write_all(tmp_path))

    assert "c4_final_holdout_family.png" in written


def _screening() -> dict[str, object]:
    cell = {
        "revision": "r1",
        "summary": "s",
        "overall": {"n": 9, "baseline_wins": 1, "candidate_wins": 2, "gains": 1, "losses": 0},
        "paired_ci": {"mean": 0.01, "ci_low": 0.0, "ci_high": 0.02},
    }
    return {"screening": {"n": 9}, "C1": cell, "C2": cell, "C3": cell, "C4": cell}
