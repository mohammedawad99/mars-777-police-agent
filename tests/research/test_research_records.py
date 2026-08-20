"""Result records, statistics, aggregation and identity, held to their contracts."""

from pathlib import Path

import pytest
from research.analysis import PRIMARY, group_by, overall, table
from research.identity import baseline_identity, digest_of
from research.manifest import manifest
from research.records import SCHEMA_VERSION, GameRecord, read_csv, write_csv, write_json
from research.stats import MIN_SAMPLE, SmallSampleError, estimate, paired_difference


def record(**overrides: object) -> GameRecord:
    fields: dict[str, object] = {
        "schema": SCHEMA_VERSION,
        "role": "police",
        "commit": "abc",
        "strategy": "CompetitiveStrategy",
        "strategy_sha256": "d" * 64,
        "opponent_family": "evasive",
        "seed_set": "development",
        "seed": 1,
        "config": "grid7",
        "grid": 7,
        "quota": 14,
        "horizon": 35,
        "outcome": "SURVIVAL",
        "captured": 0,
        "steps": 35,
        "barriers_placed": 2,
        "own_score": 5,
        "opponent_score": 10,
    }
    fields.update(overrides)
    return GameRecord(**fields)  # type: ignore[arg-type]


def test_records_round_trip_through_csv_unchanged(tmp_path: Path) -> None:
    rows = (record(), record(seed=2, outcome="CAPTURE", captured=1, own_score=20))

    path = write_csv(rows, tmp_path / "games.csv")

    assert read_csv(path) == rows


def test_a_file_from_another_schema_is_refused(tmp_path: Path) -> None:
    path = write_csv((record(schema="research-0"),), tmp_path / "games.csv")

    with pytest.raises(ValueError, match="schema"):
        read_csv(path)


def test_the_same_records_always_write_the_same_bytes(tmp_path: Path) -> None:
    rows = (record(), record(seed=2))

    first = write_csv(rows, tmp_path / "a.csv").read_bytes()
    second = write_csv(rows, tmp_path / "b.csv").read_bytes()

    assert first == second


def test_a_win_is_the_tournament_score_comparison() -> None:
    assert record(own_score=20, opponent_score=5).won == 1
    assert record(own_score=5, opponent_score=10).won == 0


def test_an_estimate_below_the_floor_reports_no_interval() -> None:
    found = estimate(tuple(float(one) for one in range(MIN_SAMPLE - 1)))

    assert found.low is None and found.high is None


def test_an_estimate_with_enough_data_reports_a_bounded_interval() -> None:
    found = estimate(tuple([1.0] * 20 + [0.0] * 20))

    assert found.low is not None and found.high is not None
    assert found.low <= found.mean <= found.high


def test_the_interval_is_the_same_on_every_run() -> None:
    values = tuple([1.0] * 20 + [0.0] * 20)

    assert estimate(values).as_record() == estimate(values).as_record()


def test_an_empty_sample_is_refused_rather_than_averaged() -> None:
    with pytest.raises(SmallSampleError):
        estimate(())


def test_a_paired_comparison_needs_matching_games() -> None:
    with pytest.raises(SmallSampleError, match="same games"):
        paired_difference((1.0, 2.0), (1.0,))


def test_a_paired_difference_is_the_per_game_difference() -> None:
    found = paired_difference(tuple([0.0] * 10), tuple([1.0] * 10))

    assert found.mean == pytest.approx(1.0)


def test_grouping_is_ordered_so_two_runs_agree() -> None:
    rows = (record(opponent_family="pursuit"), record(opponent_family="evasive"))

    assert list(group_by(rows, "opponent_family")) == ["evasive", "pursuit"]


def test_a_table_reports_the_primary_metric_for_every_group() -> None:
    rows = tuple(record(seed=one) for one in range(10))

    cells = table(rows, "opponent_family")

    assert len(cells) == 1
    assert PRIMARY in cells[0].estimates
    assert cells[0].as_row()["n"] == 10


def test_the_overall_row_covers_every_game() -> None:
    rows = tuple(record(seed=one) for one in range(12))

    assert overall(rows).estimates[PRIMARY].n == 12


def test_the_identity_names_the_strategy_composition_actually_builds() -> None:
    identity = baseline_identity()

    assert identity.strategy == "CompetitiveStrategy"
    assert len(identity.source_sha256) == 64
    assert identity.as_record()["role"] == "police"


def test_the_source_digest_depends_on_the_files_and_their_order() -> None:
    forward = digest_of(("app/competitive_strategy.py", "app/baseline_strategy.py"))
    backward = digest_of(("app/baseline_strategy.py", "app/competitive_strategy.py"))

    assert forward != backward


def test_the_manifest_identifies_every_input_by_hash() -> None:
    document = manifest().as_document()

    assert document["schema"] == SCHEMA_VERSION
    assert set(document["seed_banks"]) == {"development", "holdout", "stress"}  # type: ignore[arg-type]
    assert len(str(document["config_corpus_sha256"])) == 64


def test_a_json_document_is_written_deterministically(tmp_path: Path) -> None:
    first = write_json({"b": 1, "a": 2}, tmp_path / "a.json").read_text(encoding="utf-8")

    assert first.startswith('{\n  "a": 2')
    assert first.endswith("}\n")
