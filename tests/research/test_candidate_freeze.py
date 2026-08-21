"""The record that says exactly which candidate Stage 9B-2 is allowed to run.

A freeze is only worth anything if it pins the things that could silently
change: the source, the scenario sets, the results and the fact that the sealed
set has not been touched. Each of those is asserted here.
"""

import json
from pathlib import Path

import pytest
from research.freeze import (
    FROZEN_FIELDS,
    build,
    digest_of_file,
    manifest_digest,
)


def _artifacts(root: Path) -> None:
    (root / "candidates").mkdir(parents=True, exist_ok=True)
    for name in ("full_C4", "validation_C4", "stress_C4"):
        (root / "candidates" / f"{name}.json").write_text('{"a": 1}', encoding="utf-8")
    (root / "candidates" / "latency.json").write_text('{"b": 2}', encoding="utf-8")
    (root / "final_holdout.json").write_text(
        json.dumps({"commitment_sha256": "9" * 64, "count": 2226, "results_present": False}),
        encoding="utf-8",
    )


def test_a_file_digest_is_stable_and_content_addressed(tmp_path: Path) -> None:
    one = tmp_path / "one.json"
    one.write_text("same", encoding="utf-8")
    other = tmp_path / "other.json"
    other.write_text("same", encoding="utf-8")

    assert digest_of_file(one) == digest_of_file(other)
    assert len(digest_of_file(one)) == 64


def test_a_manifest_digest_depends_on_the_scenarios_not_their_order() -> None:
    assert manifest_digest(("b", "a")) == manifest_digest(("a", "b"))
    assert manifest_digest(("a",)) != manifest_digest(("a", "b"))


def test_the_freeze_records_every_field_stage_9b_2_needs(tmp_path: Path) -> None:
    _artifacts(tmp_path)

    found = build(tmp_path, development=("a",), validation=("b",), stress=("c",))

    for field in FROZEN_FIELDS:
        assert field in found, field
    assert found["final_holdout_evaluated"] is False
    assert found["production_promotion"] is False
    assert found["candidate"] == "C4-ablation"


def test_the_freeze_refuses_to_claim_a_holdout_that_already_has_results(
    tmp_path: Path,
) -> None:
    """A seal that reports results is not a seal, and must not be frozen against."""
    _artifacts(tmp_path)
    (tmp_path / "final_holdout.json").write_text(
        json.dumps({"commitment_sha256": "9" * 64, "count": 2226, "results_present": True}),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="results_present"):
        build(tmp_path, development=("a",), validation=("b",), stress=("c",))


def test_the_freeze_refuses_if_the_candidate_source_has_moved(tmp_path: Path) -> None:
    _artifacts(tmp_path)

    with pytest.raises(ValueError, match="no longer matches"):
        build(
            tmp_path,
            development=("a",),
            validation=("b",),
            stress=("c",),
            expect_sha256="0" * 64,
        )


def test_the_freeze_reads_the_seal_metadata_and_no_scenario_material(tmp_path: Path) -> None:
    """The sealed file carries a commitment, not a scenario list; keep it that way."""
    _artifacts(tmp_path)

    found = build(tmp_path, development=("a",), validation=("b",), stress=("c",))

    assert found["final_holdout"]["commitment_sha256"] == "9" * 64
    assert found["final_holdout"]["count"] == 2226
    assert "scenarios" not in found["final_holdout"]


def test_the_freeze_action_assesses_both_banks_and_records_the_outcome(
    tmp_path: Path,
) -> None:
    """The whole freeze path on a tiny fixture: assess, then pin."""
    from research.freeze import write_freeze
    from research.records import write_csv
    from research.validation import BANKS, FROZEN_C4_SHA256
    from test_research_records import record

    _artifacts(tmp_path)
    for bank, name in (("development", "games_development.csv"), *BANKS.items()):
        rows = tuple(record(scenario_id=f"{bank}{index:058d}", seed=index) for index in range(4))
        write_csv(rows, tmp_path / "baseline" / name)
    cell = {"n": 300, "delta": 0.06, "ci_low": 0.04, "ci_high": 0.08}
    for bank in BANKS:
        (tmp_path / "candidates" / f"{bank}_C4.json").write_text(
            json.dumps(
                {
                    "candidate_sha256": FROZEN_C4_SHA256,
                    "overall": {**cell, "low": 0.04, "high": 0.08},
                    "family": {"evasive": {**cell, "low": 0.04, "high": 0.08}},
                    "config": {"grid7": {**cell, "low": 0.04, "high": 0.08}},
                }
            ),
            encoding="utf-8",
        )
    (tmp_path / "candidates" / "latency.json").write_text(
        json.dumps({"ceiling_ms": 25.0, "grid9": {"C4": {"within_ceiling": True}}}),
        encoding="utf-8",
    )

    found = write_freeze(tmp_path)

    assert found["validated"] is True
    assert set(found["assessment"]) == set(BANKS)
    assert found["final_holdout_evaluated"] is False
    assert (tmp_path / "candidates" / "freeze_C4.json").exists()


def test_a_latency_record_outside_the_ceiling_fails_the_freeze(tmp_path: Path) -> None:
    """Gate G is read from the committed measurement, not assumed."""
    from research.freeze import _latency_ok

    (tmp_path / "candidates").mkdir(parents=True)
    (tmp_path / "candidates" / "latency.json").write_text(
        json.dumps({"ceiling_ms": 25.0, "grid11": {"C4": {"within_ceiling": False}}}),
        encoding="utf-8",
    )

    assert _latency_ok(tmp_path) is False
