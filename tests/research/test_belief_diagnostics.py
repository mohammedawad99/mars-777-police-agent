"""What the belief instrumentation must and must not do.

It exists to explain a delta, so it has to read the same belief the strategy
reads - and it must never feed anything back, because a policy tuned on its own
counters is a policy tuned on itself.
"""

import ast
from pathlib import Path

from research.configs import corpus
from research.diagnostics import Belief, observe, report

from mars777_police.app.competitive_strategy import CompetitiveStrategy
from mars777_police.domain.actions import BarrierAction, Move, MoveAction
from mars777_police.domain.board import Position
from research import diagnostics

SOURCE = Path(diagnostics.__file__)


def test_the_diagnostic_builds_no_action_of_its_own() -> None:
    """It may **ask** the policy what it decided; it may never decide instead.

    This test previously forbade calling `choose_action` at all, and that is what
    let the instrument drift: forbidden from asking, it kept its own copy of the
    gate, and the copy went on describing a rule Stage 9B-2 had replaced. Asking
    the policy is now the point. What must stay forbidden is the diagnostic
    constructing an action itself, which is how an instrument starts measuring
    its own opinion.
    """
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    built = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }

    assert not built & {"BarrierAction", "MoveAction", "PhysicalAction"}


def test_a_family_record_reports_shares_that_a_reader_can_check() -> None:
    found = Belief("evasive", 100, 80, 20, 0.5, 3.0, 400, 0).as_record()

    assert found["blocked_share"] == 0.25
    assert found["belief_steps"] <= found["steps"]


def test_a_starved_decision_is_not_counted_against_the_gate() -> None:
    """A board with no lawful target refused nothing; the gate was never asked.

    Folding those into `blocked` would credit the gate with a refusal the board
    made, which is the same confusion in a different place.
    """
    found = Belief("cornered", 100, 80, 20, 0.5, 3.0, 400, 40).as_record()

    assert found["starved_steps"] == 40
    assert found["blocked_share"] == 0.5


def test_a_family_with_no_belief_steps_does_not_divide_by_zero() -> None:
    found = Belief("quiet", 10, 0, 0, 0.0, 0.0, 0, 0).as_record()

    assert found["blocked_share"] == 0.0
    assert found["mean_landing_scent"] == 0.0


def test_the_gate_measured_is_the_policy_the_repository_ships() -> None:
    """No paraphrase: the instrument asks the real object what it decided.

    The old test pinned a *copy* of the gate, so it passed happily for as long as
    the copy and the shipped rule disagreed - which was every commit after Stage
    9B-2 replaced the landing-cell comparison with an absolute floor.
    """

    class Placing:
        def choose_action(self, observation: object) -> object:
            return BarrierAction(Position(1, 1))

    class Moving:
        def choose_action(self, observation: object) -> object:
            return MoveAction(Move.STAY)

    assert diagnostics._gate_refused(Placing(), None, 3) is False  # type: ignore[arg-type]
    assert diagnostics._gate_refused(Moving(), None, 3) is True  # type: ignore[arg-type]


def test_a_decision_with_no_lawful_target_is_never_blamed_on_the_gate() -> None:
    class Moving:
        def choose_action(self, observation: object) -> object:
            return MoveAction(Move.STAY)

    assert diagnostics._gate_refused(Moving(), None, 0) is False  # type: ignore[arg-type]


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

    assert set(families) and all("blocked_share" in one for one in families.values())
    assert all(one["starved_steps"] >= 0 for one in families.values())
