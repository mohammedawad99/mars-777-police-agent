"""The baseline decides the same thing on every machine and every run.

A policy that scored candidates by walking a set or a dict would answer
differently as `PYTHONHASHSEED` changed, and the two peers would disagree about
a game neither of them cheated at. The subprocess probes below are the only way
to prove that honestly: hash randomization is fixed at interpreter start, so an
in-process assertion cannot see it.
"""

import os
import subprocess
import sys

from strategy_builders import QUOTA, seen

from mars777_police.app.baseline_strategy import BaselineStrategy
from mars777_police.domain.board import Board, Position
from mars777_police.domain.observation import Observation
from mars777_police.domain.rules import MOVE_ORDER

SEEDS = ("0", "1", "424242")
WALLS = (Position(2, 3), Position(3, 2), Position(4, 3), Position(1, 1), Position(5, 5))

PROBE = (
    "from mars777_police.app.baseline_strategy import BaselineStrategy;"
    "from mars777_police.domain.board import Board, Position;"
    "from mars777_police.domain.barriers import BarrierQuota;"
    "from mars777_police.domain.observation import Observation;"
    "cells=[Position(2,3),Position(3,2),Position(4,3),Position(1,1),Position(5,5)];"
    "b=Board(rows=7,cols=7,blocked=frozenset(cells));"
    "o=Observation(board=b,own_position=Position(2,0),quota=BarrierQuota(14));"
    "print(BaselineStrategy().choose_action(o).move.value)"
)


def _under(seed: str) -> str:
    environment = dict(os.environ, PYTHONHASHSEED=seed)
    finished = subprocess.run(
        [sys.executable, "-c", PROBE],
        capture_output=True,
        text=True,
        check=True,
        env=environment,
    )
    return finished.stdout.strip()


def test_the_decision_survives_every_required_hash_seed() -> None:
    answers = {seed: _under(seed) for seed in SEEDS}
    assert len(set(answers.values())) == 1
    assert answers["0"] in {move.value for move in MOVE_ORDER}


def test_the_decision_matches_the_in_process_answer() -> None:
    observation = Observation(
        board=Board(rows=7, cols=7, blocked=frozenset(WALLS)),
        own_position=Position(2, 0),
        quota=QUOTA,
    )
    assert _under("0") == BaselineStrategy().choose_action(observation).move.value


def test_the_decision_is_independent_of_the_order_barriers_were_supplied_in() -> None:
    first = None
    for rotation in range(len(WALLS)):
        shuffled = WALLS[rotation:] + WALLS[:rotation]
        observation = Observation(
            board=Board(rows=7, cols=7, blocked=frozenset(shuffled)),
            own_position=Position(2, 0),
            quota=QUOTA,
        )
        chosen = BaselineStrategy().choose_action(observation)
        first = chosen if first is None else first
        assert chosen == first


def test_no_decision_anywhere_on_the_board_depends_on_a_repeated_call() -> None:
    for row in range(7):
        for col in range(7):
            observation = seen(Position(row, col), *WALLS)
            if observation.board.is_blocked(observation.own_position):
                continue
            first = BaselineStrategy().choose_action(observation)
            assert BaselineStrategy().choose_action(observation) == first
