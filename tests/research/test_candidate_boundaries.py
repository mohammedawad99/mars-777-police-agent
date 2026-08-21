"""The lines a candidate may not cross, whatever it measures.

Split from `test_candidates.py`, which proves each candidate behaves; this file
proves none of them reaches production, reaches a held-out set, or lets an
outcome influence which scenarios it was judged on.
"""

import ast
from pathlib import Path

import pytest
from research.candidates.registry import BUILDERS, CANDIDATES
from research.compare import compare, replay, replay_all
from research.records import read_csv
from research.screening import SHARE_PER_MILLE, screened
from test_research_records import record


def test_each_candidate_has_a_stable_identity_that_tracks_its_source() -> None:
    for key, entry in CANDIDATES.items():
        assert len(entry.source_sha256) == 64
        assert entry.as_record()["candidate"].startswith(key)


def test_production_composition_still_selects_the_frozen_strategy() -> None:
    """No candidate may become the tournament policy in this stage."""
    src = Path(__file__).resolve().parents[2] / "src" / "mars777_police"
    body = (src / "composition.py").read_text(encoding="utf-8")

    assert "CompetitiveStrategy()," in body
    assert "PursuitMover" not in body
    assert "DenialStrategy" not in body


def test_no_production_module_imports_a_candidate() -> None:
    """Checked as imports, not as text.

    `baseline_strategy` legitimately writes "Candidates come from `legal_moves`",
    and a guard that failed on that would teach the next author to delete the
    sentence rather than keep the boundary.
    """
    src = Path(__file__).resolve().parents[2] / "src" / "mars777_police"
    reachers: list[str] = []
    for path in src.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            named: set[str] = set()
            if isinstance(node, ast.Import):
                named = {alias.name for alias in node.names}
            elif isinstance(node, ast.ImportFrom):
                named = {node.module or ""}
            if any("research" in one or "candidates" in one for one in named):
                reachers.append(path.name)

    assert reachers == []


def test_screening_membership_is_blind_to_outcomes() -> None:
    """Chosen from the identity alone, so no result can influence the subset."""
    won = record(scenario_id="s1", outcome="CAPTURE", own_score=20)
    lost = record(scenario_id="s1", outcome="SURVIVAL", own_score=5)

    assert screened(won.scenario_id) == screened(lost.scenario_id)
    assert 0 < SHARE_PER_MILLE < 1000


def test_a_paired_comparison_refuses_scenarios_that_do_not_line_up() -> None:
    left = (record(scenario_id="a"),)
    right = (record(scenario_id="b"),)

    with pytest.raises(ValueError, match="same scenarios"):
        compare(left, right)


def test_the_committed_baseline_rows_predate_the_promotion_and_say_so() -> None:
    """The pairing machinery is a no-op for the policy that produced the rows.

    That policy is no longer `CompetitiveStrategy`: Stage 9B-2 promoted the C4
    barrier rule into it, so the shipped class now decides differently from the
    rows committed at Stage 9B-0. The rows remain valid historical evidence -
    every paired comparison in the research record was measured against them -
    and they carry the identity of the strategy that produced them, which is
    what makes that still checkable.
    """
    root = Path(__file__).resolve().parents[2] / "results" / "baseline"
    if not (root / "games_development.csv").exists():
        pytest.skip("no committed development rows in this working tree")
    rows = tuple(read_csv(root / "games_development.csv"))[:12]

    assert {one.strategy for one in rows} == {"CompetitiveStrategy"}
    assert len({one.strategy_sha256 for one in rows}) == 1


def test_a_replay_is_a_no_op_for_the_policy_that_produced_its_rows() -> None:
    """Determinism of the pairing machinery, on rows this policy really produced."""
    from research.candidates.registry import BUILDERS

    root = Path(__file__).resolve().parents[2] / "results" / "candidates"
    if not (root / "full_C4.csv").exists():
        pytest.skip("no committed candidate rows in this working tree")
    rows = tuple(read_csv(root / "full_C4.csv"))[:12]
    identity = (rows[0].strategy, rows[0].strategy_sha256)

    again = replay_all(BUILDERS["C4"](), rows, identity)

    assert [one.outcome for one in again] == [one.outcome for one in rows]
    assert [one.barriers_placed for one in again] == [one.barriers_placed for one in rows]


def test_a_replayed_row_is_filed_under_the_policy_that_produced_it() -> None:
    """Not under the baseline it was paired against."""
    from research.records import GameRecord
    from test_research_records import record

    row: GameRecord = record(strategy="CompetitiveStrategy", strategy_sha256="d" * 64)

    again = replay(BUILDERS["C4"](), row, ("C4-ablation", "e" * 64))

    assert again.strategy == "C4-ablation"
    assert again.strategy_sha256 == "e" * 64
    assert again.scenario_id == row.scenario_id
