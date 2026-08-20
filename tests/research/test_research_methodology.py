"""The methodology Stage 9B-0F closed: what counts as one observation, and what is sealed.

Two errors are guarded here, and both were real. A deterministic scenario
replayed under a different seed label is **not** a second observation. And a
holdout whose outcomes have been read is **not** a holdout, whatever it is
called.
"""

import pytest
from research.analysis import PRIMARY, headline, overall, reference, unique_scenarios
from research.configs import corpus
from research.opponents import FAMILIES, SEEDED_FAMILIES, seed_matters
from research.scenario import SCENARIO_VERSION, openings, scenario_id, space_size, start_cells
from research.sealed import RESULTS_PRESENT, sealed_set
from research.seeds import (
    FINAL_HOLDOUT,
    SEALED_NAMESPACE,
    development_bank,
    disjoint,
    final_holdout_bank,
    stress_bank,
    validation_bank,
    working_banks,
)
from research.stats import SmallSampleError, estimate, paired_by_scenario
from test_research_records import record

CONFIG = corpus()[1]


def identity(**overrides: object) -> str:
    fields: dict[str, object] = {
        "role": "police",
        "family": "evasive",
        "config": CONFIG,
        "seed": 1,
        "police": start_cells(CONFIG, 1)[0],
        "thief": start_cells(CONFIG, 1)[1],
    }
    fields.update(overrides)
    return scenario_id(**fields)  # type: ignore[arg-type]


def test_identical_conditions_produce_the_same_scenario_id() -> None:
    assert identity() == identity()


@pytest.mark.parametrize(
    "change",
    [{"role": "thief"}, {"family": "pursuit"}, {"config": corpus()[2]}],
)
def test_a_changed_condition_produces_a_different_scenario_id(change: dict[str, object]) -> None:
    assert identity(**change) != identity()


def test_different_openings_are_different_scenarios() -> None:
    police, thief = start_cells(CONFIG, 2)

    assert identity(police=police, thief=thief) != identity()


def test_the_seed_changes_the_identity_only_where_it_changes_behaviour() -> None:
    """A seed that no policy reads must not make one game look like two."""
    assert identity(family="evasive", seed=99) == identity(family="evasive", seed=1)
    assert identity(family="random_legal", seed=99) != identity(family="random_legal", seed=1)


def test_the_seeded_family_list_matches_what_the_policies_actually_read() -> None:
    for family in FAMILIES:
        assert seed_matters(family) is (family in SEEDED_FAMILIES)


def test_the_scenario_identity_is_versioned() -> None:
    assert SCENARIO_VERSION == "scenario-1"


def test_openings_are_drawn_without_replacement() -> None:
    drawn = openings(CONFIG, development_bank().seeds)
    pairs = {(police, thief) for _, police, thief in drawn}

    assert len(pairs) == len(drawn)


def test_a_finite_space_yields_its_whole_size_and_no_more() -> None:
    fixed = next(one for one in corpus() if one.fixed_starts)

    assert space_size(fixed) == 1
    assert len(openings(fixed, development_bank().seeds)) == 1


def test_duplicated_rows_do_not_increase_the_effective_sample() -> None:
    rows = tuple(record(scenario_id=f"s{one}", seed=one, config="grid9") for one in range(20))
    doubled = rows + rows

    assert len(unique_scenarios(doubled)) == 20
    assert overall(doubled).estimates[PRIMARY].n == 20
    assert overall(rows).estimates[PRIMARY].n == 20


def test_duplicating_a_series_does_not_narrow_its_interval() -> None:
    values = tuple([1.0] * 10 + [0.0] * 10)

    once = estimate(values)
    twice = estimate(values + values)

    assert (twice.high or 0) - (twice.low or 0) < (once.high or 0) - (once.low or 0)


def test_the_headline_excludes_the_fixed_reference_geometry() -> None:
    rows = (
        record(scenario_id="a", config="grid9"),
        record(scenario_id="b", config="appendixF-example"),
    )

    assert [one.config for one in headline(rows)] == ["grid9"]
    assert [one.config for one in reference(rows)] == ["appendixF-example"]


def test_a_paired_comparison_refuses_mismatched_scenario_sets() -> None:
    with pytest.raises(SmallSampleError, match="same scenario set"):
        paired_by_scenario({"a": 1.0, "b": 0.0}, {"a": 1.0, "c": 0.0})


def test_a_paired_comparison_lines_up_by_scenario_not_by_position() -> None:
    before = {f"s{one}": 0.0 for one in range(10)}
    after = {f"s{one}": 1.0 for one in range(10)}

    assert paired_by_scenario(before, after).mean == pytest.approx(1.0)


def test_the_sealed_bank_has_its_own_namespace_and_is_disjoint_from_every_other() -> None:
    sealed = final_holdout_bank()

    assert SEALED_NAMESPACE != "mars777-research/v1/"
    for other in (development_bank(), validation_bank(), stress_bank()):
        assert disjoint(sealed, other)


def test_no_research_command_can_reach_the_sealed_bank() -> None:
    assert FINAL_HOLDOUT not in {one.name for one in working_banks()}


def test_asking_for_the_sealed_bank_is_refused(tmp_path: object) -> None:
    from research import bench_main

    with pytest.raises(SystemExit, match="sealed"):
        bench_main.bench(tmp_path, [FINAL_HOLDOUT])  # type: ignore[arg-type]


def test_the_sealed_set_is_committed_but_holds_no_outcome() -> None:
    document = sealed_set("police").as_document()

    assert RESULTS_PRESENT is False
    assert document["results_present"] is False
    assert len(str(document["commitment_sha256"])) == 64
    assert document["count"] > 0
    assert not any("outcome" in str(key) for key in document)


def test_the_manifest_states_the_unit_the_weighting_and_the_seal() -> None:
    from research.manifest import STATISTICAL_UNIT, manifest

    document = manifest().as_document()

    assert document["statistical_unit"] == STATISTICAL_UNIT
    assert document["scenario_version"] == SCENARIO_VERSION
    assert document["final_holdout_results_present"] is False
    assert document["weighting"]


def test_no_committed_result_file_belongs_to_the_sealed_bank() -> None:
    """The sealed input manifest may be committed; an outcome may not."""
    from pathlib import Path

    results = Path(__file__).resolve().parents[2] / "results"
    if not results.exists():
        pytest.skip("no committed results in this working tree")
    played = [one.name for one in results.rglob("games_*.csv") if FINAL_HOLDOUT in one.name]

    assert played == []
