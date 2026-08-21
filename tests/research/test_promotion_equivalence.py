"""The promoted production policy is the frozen research candidate, exactly.

The final-holdout number belongs to `C4-ablation r1`. Production may only claim
it if production *is* that behaviour, so this compares the two on the same
lawful observations and requires identical actions - never a similar rate, and
never the sealed set, which is consumed.
"""

from decimal import Decimal
from pathlib import Path

import pytest
from research.candidates import denial
from research.candidates.registry import BUILDERS, CANDIDATES
from research.compare import replay
from research.records import read_csv
from research.validation import BANKS, FROZEN_C4_SHA256

from mars777_police.app.competitive_strategy import (
    CONSERVATIVE,
    TRAP_BONUS,
    CompetitiveStrategy,
)
from mars777_police.domain.barriers import BarrierQuota
from mars777_police.domain.board import Board, Position
from mars777_police.domain.observation import Observation
from mars777_police.domain.scent import ScentField
from mars777_police.domain.scent_belief import ScentBelief

ROOT = Path(__file__).resolve().parents[2]
PROMOTED = CompetitiveStrategy()
FROZEN = BUILDERS["C4"]()
WEIGHTS = ("0", "0.05", "0.1", "0.3", "0.9")


def _view(shape: Board, cell: Position, weights: dict[Position, str]) -> Observation:
    grid = tuple(
        tuple(Decimal(weights.get(Position(r, c), "0")) for c in range(shape.cols))
        for r in range(shape.rows)
    )
    return Observation(
        board=shape,
        own_position=cell,
        quota=BarrierQuota(14),
        scent=ScentBelief(ScentField(shape.rows, shape.cols, 0, grid), 1),
    )


def test_the_promoted_parameters_are_the_frozen_ones() -> None:
    assert CONSERVATIVE == denial.CONSERVATIVE == Decimal("0.9")
    assert TRAP_BONUS == denial.TRAP_BONUS == Decimal(10)
    assert CANDIDATES["C4"].source_sha256 == FROZEN_C4_SHA256


def test_the_two_agree_on_an_exhaustive_small_state_matrix() -> None:
    """Every actor cell x every single-source belief on a 5x5 board."""
    shape = Board(rows=5, cols=5)
    compared = 0
    for row in range(5):
        for col in range(5):
            actor = Position(row, col)
            for hot_row in range(5):
                for hot_col in range(5):
                    for weight in WEIGHTS:
                        view = _view(shape, actor, {Position(hot_row, hot_col): weight})
                        assert PROMOTED.choose_action(view) == FROZEN.choose_action(view)
                        compared += 1

    assert compared == 5 * 5 * 5 * 5 * len(WEIGHTS)


def test_the_two_agree_when_the_board_carries_walls_and_traps() -> None:
    """Barrier-dense states are where the trap term and legality interact."""
    walls = (
        frozenset({Position(1, 0)}),
        frozenset({Position(1, 0), Position(0, 1)}),
        frozenset({Position(2, 1), Position(1, 2), Position(3, 2)}),
        frozenset({Position(0, c) for c in range(5)}),
    )
    for blocked in walls:
        shape = Board(rows=5, cols=5, blocked=blocked)
        for row in range(5):
            for col in range(5):
                actor = Position(row, col)
                if actor in blocked:
                    continue
                for weight in ("0.1", "0.9"):
                    hot = {Position(0, 0): weight, Position(4, 4): "0.3"}
                    view = _view(shape, actor, hot)
                    assert PROMOTED.choose_action(view) == FROZEN.choose_action(view)


@pytest.mark.parametrize("bank", ["development", *BANKS])
def test_the_two_play_committed_scenarios_identically(bank: str) -> None:
    """Whole games on real research scenarios, outcome for outcome.

    A sample rather than the corpus: equivalence is a property of the decision
    function, already exhausted above, and replaying thousands of games here
    would move a research benchmark into the gating suite.
    """
    name = "games_development.csv" if bank == "development" else BANKS[bank]
    path = ROOT / "results" / "baseline" / name
    if not path.exists():
        pytest.skip(f"no committed {bank} rows in this working tree")
    rows = tuple(read_csv(path))[:24]
    identity = ("C4-ablation", FROZEN_C4_SHA256)

    for row in rows:
        mine = replay(PROMOTED, row, identity)
        theirs = replay(FROZEN, row, identity)

        assert mine.outcome == theirs.outcome
        assert mine.steps == theirs.steps
        assert mine.barriers_placed == theirs.barriers_placed
        assert mine.own_score == theirs.own_score


def test_equivalence_is_established_only_on_banks_that_may_be_replayed() -> None:
    """The holdout is consumed, so equivalence may never appeal to it.

    Asserted on the parametrisation this module actually runs rather than on its
    own source text - a guard that grepped this file would match the very string
    it uses to describe what it forbids.
    """
    marks = test_the_two_play_committed_scenarios_identically.pytestmark
    banks = {value for mark in marks for value in mark.args[1]}

    assert banks == {"development", "validation", "stress"}
    assert "final_holdout" not in banks


def test_the_tournament_composition_builds_the_promoted_behaviour() -> None:
    """No research flag, no environment switch, no benchmark mode.

    The strategy the strict, autonomous and public paths use is whatever
    `compose_agent` installs, and it must be the promoted policy itself.
    """
    import inspect

    from mars777_police import composition

    body = inspect.getsource(composition)
    assert "CompetitiveStrategy()," in body
    assert "research" not in body
    assert "MARS777_STRATEGY" not in body
