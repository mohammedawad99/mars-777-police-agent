"""The police baseline: stand where the most of the board is within easy reach.

Knowing nothing about the thief, the only defensible thing a pursuer can do is
be *reachable* - minimise the total barrier-aware distance from where it stands
to every cell it could still be called to. That is a PROJECT-DERIVED baseline,
not a lecturer-mandated algorithm, and it is deliberately weak: with no belief
it has no target, so once it is already the most central cell it stays there.
The tests below pin that behaviour rather than hide it, because the belief stage
replaces the uniform target set and inherits this same comparison.
"""

import pytest
from strategy_builders import (
    CENTRE,
    LIMITS,
    QUOTA,
    board,
    column,
    destination,
    manhattan_spread,
    seen,
)

from mars777_police.app.baseline_strategy import BaselineStrategy
from mars777_police.app.protocol_errors import LocalDefectError
from mars777_police.app.turn_service import LocalTurnService
from mars777_police.domain.actions import BarrierAction, MoveAction
from mars777_police.domain.board import Position
from mars777_police.domain.observation import Observation
from mars777_police.domain.reachability import reachable_from
from mars777_police.domain.rules import MOVE_ORDER, Move, legal_moves
from mars777_police.domain.truth import LocalTruth

POLICE = BaselineStrategy()


def _spread(observation: Observation, move: Move) -> int:
    return sum(reachable_from(observation.board, destination(observation, move)).values())


def test_it_returns_a_legal_move_on_an_open_board() -> None:
    action = POLICE.choose_action(seen(CENTRE))
    assert isinstance(action, MoveAction)
    assert action.move in legal_moves(board(), CENTRE)


def test_the_chosen_action_is_accepted_by_the_turn_service() -> None:
    truth = LocalTruth(board=board(), own_position=Position(3, 0))
    action = POLICE.choose_action(seen(Position(3, 0)))
    result = LocalTurnService(limits=LIMITS, quota=QUOTA).apply(truth, action)
    assert result.completed_step == 1


def test_the_same_observation_always_yields_the_same_action() -> None:
    observation = seen(Position(1, 5), Position(2, 2), Position(4, 4))
    first = POLICE.choose_action(observation)
    for _ in range(10):
        assert POLICE.choose_action(observation) == first


def test_it_walks_toward_the_reachable_centre_rather_than_the_first_legal_move() -> None:
    observation = seen(Position(3, 0))
    assert legal_moves(observation.board, observation.own_position)[0] is Move.N
    assert POLICE.choose_action(observation) == MoveAction(Move.E)


def test_a_tie_is_broken_by_the_existing_move_order() -> None:
    observation = seen(Position(3, 0), Position(3, 1))
    reachable = legal_moves(board(Position(3, 1)), Position(3, 0))
    scored = {move: _spread(observation, move) for move in reachable}
    best = min(scored.values())
    tied = [move for move in MOVE_ORDER if scored.get(move) == best]
    assert len(tied) > 1
    assert POLICE.choose_action(observation) == MoveAction(tied[0])


def test_it_stays_when_staying_is_the_only_legal_action() -> None:
    observation = seen(Position(0, 0), Position(0, 1), Position(1, 0))
    assert legal_moves(observation.board, observation.own_position) == (Move.STAY,)
    assert POLICE.choose_action(observation) == MoveAction(Move.STAY)


def test_it_stays_once_it_is_already_the_most_reachable_cell() -> None:
    assert POLICE.choose_action(seen(CENTRE)) == MoveAction(Move.STAY)


def test_a_barrier_changes_the_decision_it_would_otherwise_have_made() -> None:
    open_board = POLICE.choose_action(seen(Position(2, 0)))
    walled = POLICE.choose_action(seen(Position(2, 0), *column(1, 0, 1, 2, 3)))
    assert open_board != walled


def test_the_objective_is_barrier_aware_and_not_a_manhattan_shortcut() -> None:
    wall = column(3, 0, 1, 2, 3, 4, 5)
    observation = seen(Position(3, 1), *wall)
    moves = legal_moves(observation.board, observation.own_position)
    walked = min(moves, key=lambda move: _spread(observation, move))
    flat = min(
        moves,
        key=lambda move: manhattan_spread(observation.board, destination(observation, move)),
    )
    assert walked is not flat
    assert POLICE.choose_action(observation) == MoveAction(walked)


def test_it_never_proposes_a_barrier_anywhere_on_any_reachable_board() -> None:
    for row in range(7):
        for col in range(7):
            here = Position(row, col)
            observation = seen(here, Position(2, 2), Position(4, 4), Position(1, 5))
            if not legal_moves(observation.board, here):
                continue
            assert not isinstance(POLICE.choose_action(observation), BarrierAction)


def test_it_refuses_rather_than_inventing_a_stay_when_there_is_no_legal_action() -> None:
    trapped = seen(Position(0, 0), Position(0, 0), Position(0, 1), Position(1, 0))
    assert legal_moves(trapped.board, trapped.own_position) == ()
    with pytest.raises(LocalDefectError, match="no legal action"):
        POLICE.choose_action(trapped)
