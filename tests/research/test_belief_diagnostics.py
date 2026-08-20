"""What the belief instrumentation must and must not do.

It exists to explain a delta, so it has to read the same belief the strategy
reads - and it must never feed anything back, because a policy tuned on its own
counters is a policy tuned on itself.
"""

import ast
from decimal import Decimal
from pathlib import Path

from research.configs import corpus
from research.diagnostics import Belief, observe, report

from mars777_police.app.competitive_strategy import CompetitiveStrategy
from research import diagnostics

SOURCE = Path(diagnostics.__file__)


def test_the_diagnostic_never_chooses_an_action() -> None:
    """Read-only by construction, asserted on the source rather than promised."""
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    called = {
        node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }

    assert "choose_action" not in called


def test_a_family_record_reports_shares_that_a_reader_can_check() -> None:
    found = Belief("evasive", 100, 80, 20, 0.5, 3.0, 400).as_record()

    assert found["blocked_share"] == 0.25
    assert found["belief_steps"] <= found["steps"]


def test_a_family_with_no_belief_steps_does_not_divide_by_zero() -> None:
    found = Belief("quiet", 10, 0, 0, 0.0, 0.0, 0).as_record()

    assert found["blocked_share"] == 0.0
    assert found["mean_landing_scent"] == 0.0


def test_the_gate_test_matches_the_shipped_rule() -> None:
    """The instrument must model the production gate, not a paraphrase of it."""
    cold = ((object(), Decimal("0.10")),)

    assert diagnostics._would_block(cold, Decimal("0.90")) is True
    assert diagnostics._would_block(cold, Decimal("0.05")) is False
    assert diagnostics._would_block((), Decimal(0)) is True


def test_observing_one_family_counts_every_step_of_every_game() -> None:
    found = observe(CompetitiveStrategy(), corpus()[0], "evasive", range(7, 9))

    assert found.family == "evasive"
    assert found.steps > 0
    assert found.belief_steps <= found.steps
    assert found.blocked_steps <= found.belief_steps


def test_the_written_report_is_labelled_development_only(tmp_path: Path) -> None:
    written = report(CompetitiveStrategy(), corpus()[0], ("evasive",), tmp_path / "belief.json")
    body = written.read_text(encoding="utf-8")

    assert "not final holdout" in body
    assert "not a production promotion" in body


def test_the_committed_diagnostic_shows_the_family_that_motivated_the_candidate() -> None:
    """The measured claim the whole stage rests on, asserted against the artifact."""
    import json

    path = Path(__file__).resolve().parents[2] / "results" / "candidates" / "belief.json"
    if not path.exists():
        import pytest

        pytest.skip("no committed diagnostic in this working tree")
    families = {
        one["family"]: one for one in json.loads(path.read_text(encoding="utf-8"))["families"]
    }

    assert families["adversarial_corner"]["blocked_share"] > 0.5
    assert all(
        one["blocked_share"] < 0.2 for name, one in families.items() if name != "adversarial_corner"
    )
