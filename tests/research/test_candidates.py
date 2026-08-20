"""What every police candidate must be, before any of them is measured.

A candidate that saw more than the shipped agent, or acted illegally, or
answered differently on two identical inputs would make its benchmark number
meaningless. So those properties are asserted here rather than assumed from a
green benchmark.
"""

import ast
from decimal import Decimal
from pathlib import Path

import pytest
from research.candidates import denial, pursuit
from research.candidates.pursuit import PursuitMover
from research.candidates.registry import BUILDERS
from research.configs import corpus
from research.game import SubGame
from research.opponents import opponent
from research.scenario import start_cells

from mars777_police.app.baseline_strategy import BaselineStrategy
from mars777_police.app.competitive_strategy import CompetitiveStrategy
from mars777_police.domain.actions import BarrierAction, MoveAction
from mars777_police.domain.barriers import is_placeable
from mars777_police.domain.board import Position
from mars777_police.domain.observation import Observation
from mars777_police.domain.rules import legal_moves

CANDIDATE_DIR = Path(__file__).resolve().parents[2] / "research" / "candidates"
CONFIG = corpus()[1]


def observation_at(step: int = 3):  # type: ignore[no-untyped-def]
    """A lawful observation taken from a real game, after some belief exists."""
    from mars777_police.app.sealed_record_values import ActorRole

    police, thief = start_cells(CONFIG, 5)
    game = SubGame(CONFIG, CompetitiveStrategy(), opponent("evasive", 5), police, thief)
    for _ in range(step):
        game.play_round()
    return game.observation(ActorRole.POLICE)


@pytest.mark.parametrize("key", sorted(BUILDERS))
def test_every_candidate_answers_the_same_way_twice(key: str) -> None:
    view = observation_at()
    policy = BUILDERS[key]()

    assert policy.choose_action(view) == policy.choose_action(view)


@pytest.mark.parametrize("key", sorted(BUILDERS))
def test_every_candidate_returns_only_a_locally_legal_action(key: str) -> None:
    view = observation_at()

    action = BUILDERS[key]().choose_action(view)

    if isinstance(action, MoveAction):
        assert action.move in legal_moves(view.board, view.own_position)
    else:
        assert isinstance(action, BarrierAction)
        assert is_placeable(view.board, view.own_position, action.target, view.quota)


@pytest.mark.parametrize("key", sorted(BUILDERS))
def test_no_candidate_names_anything_it_may_not_know(key: str) -> None:
    forbidden = ("cell_of", "thief_cell", "police_cell", "opponent_position", "nonce", "replay")
    for path in CANDIDATE_DIR.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        names = {node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)}
        assert not (names & set(forbidden)), path.name


def test_the_pursuit_objective_prefers_moving_toward_the_belief() -> None:
    """The whole point of C1's mover, asserted on the formula itself."""
    mass = ((Position(8, 8), Decimal("0.9")),)

    near = pursuit.pursuit_cost(Position(7, 8), mass)
    far = pursuit.pursuit_cost(Position(1, 1), mass)

    assert near < far


def test_the_pursuit_mover_refuses_to_invent_a_move_when_trapped() -> None:
    """A trapped actor is a terminal the caller settles, not a decision (App E #47)."""
    from mars777_police.domain.barriers import BarrierQuota
    from mars777_police.domain.board import Board

    walls = frozenset({Position(0, 0), Position(0, 1), Position(1, 0)})
    walled = Board(rows=7, cols=7, blocked=walls)
    boxed = Observation(walled, Position(0, 0), BarrierQuota(max_barriers=14))
    assert legal_moves(walled, Position(0, 0)) == ()

    with pytest.raises(ValueError, match="terminal"):
        PursuitMover().choose_action(boxed)


def test_a_silent_sub_game_gives_every_move_the_same_pursuit_cost() -> None:
    """With no evidence C1 must fall through to the baseline ordering exactly."""
    assert pursuit.pursuit_cost(Position(0, 0), ()) == Decimal(0)
    assert pursuit.pursuit_cost(Position(5, 5), ()) == Decimal(0)


def test_the_denial_rule_refuses_to_place_when_nothing_is_believed() -> None:
    """No belief means no expected value, so C2/C3/C4 must move instead."""
    from mars777_police.domain.barriers import BarrierQuota
    from mars777_police.domain.board import Board
    from mars777_police.domain.observation import Observation

    silent = Observation(Board(rows=9, cols=9), Position(4, 4), BarrierQuota(max_barriers=14))

    for threshold in (denial.CONSERVATIVE, denial.AGGRESSIVE):
        assert isinstance(denial.DenialStrategy(threshold).choose_action(silent), MoveAction)


def test_the_aggressive_threshold_is_strictly_easier_than_the_conservative_one() -> None:
    """C3 must differ from C2 by its floor, not by a different rule."""
    assert denial.AGGRESSIVE < denial.CONSERVATIVE
    assert denial.TRAP_BONUS > denial.CONSERVATIVE


def test_a_trap_is_worth_far_more_than_a_nudge() -> None:
    """`GAME-005` ends the game; a mobility reduction only shrinks the room."""
    assert Decimal(10) <= denial.TRAP_BONUS


def test_the_ablation_uses_the_shipped_mover_and_the_candidate_rule() -> None:
    """C4 exists to say which half of C2 carries the gain."""
    built = BUILDERS["C4"]()

    assert isinstance(built, denial.DenialStrategy)
    assert type(built.mover) is BaselineStrategy
    assert built.threshold == denial.CONSERVATIVE
