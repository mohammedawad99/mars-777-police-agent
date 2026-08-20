"""The whole research pipeline end to end, on a bank small enough to run twice.

What is proved here is the property the stage actually needs: that one documented
command turns a frozen strategy into result rows, tables, figures, a latency
record and a manifest - and that running it again produces the same bytes.
"""

import json
from pathlib import Path

import pytest
from research.charts import Bar, bar_chart, save
from research.configs import corpus
from research.identity import baseline_identity, commit_of
from research.latency import measure
from research.records import read_csv
from research.runner import OPPONENT_ROLE, OWN_ROLE, Sweep, size_of

from research import bench_main, seeds, tables


@pytest.fixture
def tiny(monkeypatch: pytest.MonkeyPatch) -> None:
    """Shrink every bank to two seeds so the pipeline runs inside a test."""
    monkeypatch.setattr(seeds, "DEVELOPMENT_SIZE", 2)
    monkeypatch.setattr(seeds, "HOLDOUT_SIZE", 2)
    monkeypatch.setattr(seeds, "STRESS_SIZE", 1)


def test_a_sweep_plays_exactly_the_games_it_promised(tiny: None) -> None:
    bank = seeds.bank("development", 2)
    records = Sweep(baseline_identity(), bench_main.strategy(), bank).run()

    assert len(records) == size_of(bank)
    assert {one.seed_set for one in records} == {"development"}


def test_the_two_roles_are_opposites_whichever_repository_this_is() -> None:
    assert OWN_ROLE is not OPPONENT_ROLE


def test_the_documented_command_produces_every_committed_artifact(
    tiny: None, tmp_path: Path
) -> None:
    assert bench_main.main(["all", "--out", str(tmp_path)]) == 0

    assert (tmp_path / "manifest.json").exists()
    assert (tmp_path / "baseline" / "latency.json").exists()
    assert (tmp_path / "tables" / "overall.json").exists()
    assert sorted(one.name for one in (tmp_path / "figures").glob("*.png"))
    rows = read_csv(tmp_path / "baseline" / "games_development.csv")
    assert rows and rows[0].schema


def test_running_the_pipeline_twice_produces_the_same_tables(tiny: None, tmp_path: Path) -> None:
    bench_main.main(["all", "--out", str(tmp_path / "first")])
    bench_main.main(["all", "--out", str(tmp_path / "second")])

    for name in ("tables/by_opponent_family.csv", "baseline/games_development.csv"):
        first = (tmp_path / "first" / name).read_bytes()
        assert first == (tmp_path / "second" / name).read_bytes()


def test_analysis_alone_regenerates_from_committed_rows(tiny: None, tmp_path: Path) -> None:
    bench_main.main(["bench", "--out", str(tmp_path)])
    (tmp_path / "tables").mkdir(exist_ok=True)

    assert bench_main.main(["analyse", "--out", str(tmp_path)]) == 0
    assert json.loads((tmp_path / "tables" / "overall.json").read_text())["games"] > 0


def test_a_named_seed_set_can_be_run_alone(tiny: None, tmp_path: Path) -> None:
    bench_main.bench(tmp_path, ["stress"])

    assert (tmp_path / "baseline" / "games_stress.csv").exists()
    assert not (tmp_path / "baseline" / "games_holdout.csv").exists()


def test_analysing_an_empty_root_refuses_rather_than_inventing_a_table(
    tmp_path: Path,
) -> None:
    with pytest.raises(SystemExit, match="no benchmark records"):
        bench_main.load(tmp_path)


def test_the_command_refuses_an_unknown_action() -> None:
    with pytest.raises(SystemExit):
        bench_main.parse_args(["invent"])


def test_latency_is_measured_at_the_production_call_surface() -> None:
    found = measure(bench_main.strategy(), corpus()[0], seed=3)

    assert found.samples >= 200
    assert 0.0 <= found.median_ms <= found.p95_ms <= found.max_ms
    assert set(found.as_record()) == {"samples", "median_ms", "p95_ms", "max_ms"}


def test_a_figure_is_drawn_deterministically_and_written(tmp_path: Path) -> None:
    bars = (Bar("evasive", 0.25, 0.2, 0.3, 100), Bar("pursuit", 0.5, None, None, 4))

    frame = bar_chart("win rate by family", "win rate", bars, "baseline")
    first = save(frame, tmp_path / "a.png").read_bytes()

    assert (
        first
        == save(
            bar_chart("win rate by family", "win rate", bars, "baseline"), tmp_path / "b.png"
        ).read_bytes()
    )
    assert "win rate by family" in frame.title


def test_a_figure_with_no_measured_group_is_refused() -> None:
    with pytest.raises(ValueError, match="at least one measured group"):
        bar_chart("empty", "unit", (), "baseline")


def test_the_figure_states_its_sample_size_and_baseline() -> None:
    frame = bar_chart("t", "win rate", (Bar("evasive", 0.25, None, None, 42),), "police baseline")
    words = " ".join(one.value for one in frame.texts)

    assert "n=42" in words
    assert "police baseline" in words
    assert "bars start at zero" in words


def test_tables_are_written_for_every_documented_grouping(tiny: None, tmp_path: Path) -> None:
    records = Sweep(baseline_identity(), bench_main.strategy(), seeds.bank("development", 2)).run()

    tables.write_all(records, tmp_path)

    for key in tables.GROUPS:
        assert (tmp_path / "tables" / f"by_{key}.csv").exists()


def test_the_commit_is_reported_even_outside_a_repository(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def refuse(*args: object, **kwargs: object) -> object:
        raise OSError("no git here")

    monkeypatch.setattr("subprocess.run", refuse)

    assert commit_of() == "unknown"


def test_the_research_command_is_runnable_as_a_module(tiny: None, tmp_path: Path) -> None:
    """`uv run python -m research.bench_main` really is the documented entry point.

    Only the analysis stage is run here: playing a full bank in a test would
    turn a unit suite into a benchmark, and the sweep itself is covered above.
    """
    import os
    import subprocess
    import sys

    bench_main.bench(tmp_path, ["stress"])
    root = Path(__file__).resolve().parents[2]
    finished = subprocess.run(
        [sys.executable, "-m", "research.bench_main", "analyse", "--out", str(tmp_path)],
        capture_output=True,
        text=True,
        check=False,
        cwd=root,
        env={**os.environ, "PYTHONPATH": str(root)},
    )

    assert finished.returncode == 0, finished.stderr
    assert "analysed" in finished.stdout
    assert (tmp_path / "manifest.json").exists()
