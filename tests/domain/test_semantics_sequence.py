"""Sequence and invariant tests across the Stage-3B semantics.

Barrier -> movement legality, terminal -> score, multi-turn scent traces and
stability under hash randomisation - with no orchestration.
"""

import os
import subprocess
import sys
from decimal import Decimal

from mars777_police.domain.barriers import BarrierQuota, is_placeable, place_barrier
from mars777_police.domain.board import Board, Position
from mars777_police.domain.rules import Move, is_legal_move, legal_moves
from mars777_police.domain.scent import ScentField, ScentKernel, ScentParams
from mars777_police.domain.scoring import score_for
from mars777_police.domain.terminal import (
    Outcome,
    TurnLimits,
    evaluate_terminal,
    is_barrier_capture,
    is_trapped,
)

GRID = 7
ACTOR = Position(3, 3)
QUOTA = BarrierQuota(max_barriers=14)
PARAMS = ScentParams()
KERNEL = ScentKernel.from_rows(
    (
        ("0.0", "0.1", "0.2", "0.1", "0.0"),
        ("0.1", "0.3", "0.5", "0.3", "0.1"),
        ("0.2", "0.5", "0.9", "0.5", "0.2"),
        ("0.1", "0.3", "0.5", "0.3", "0.1"),
        ("0.0", "0.1", "0.2", "0.1", "0.0"),
    ),
)

PROBE = (
    "from mars777_police.domain.board import Board, Position;"
    "from mars777_police.domain.barriers import BarrierQuota, place_barrier;"
    "from mars777_police.domain.rules import legal_moves;"
    "from mars777_police.domain.scent import ScentField, ScentKernel, ScentParams;"
    "b=place_barrier(Board(rows=7,cols=7), Position(3,3), Position(2,3),"
    " BarrierQuota(max_barriers=14));"
    "k=ScentKernel.from_rows(tuple(tuple('0.9' if (r,c)==(2,2) else '0.1'"
    " for c in range(5)) for r in range(5)));"
    "f=ScentField.zero(b).evolve(k,(Position(3,3),Position(1,1)),ScentParams());"
    "print([m.value for m in legal_moves(b, Position(3,3))], str(f.at(Position(3,3))))"
)


def _board(blocked: frozenset[Position] = frozenset()) -> Board:
    return Board(rows=GRID, cols=GRID, blocked=blocked)


def test_placing_a_barrier_makes_that_move_illegal() -> None:
    board = _board()
    assert is_legal_move(board, ACTOR, Move.N)
    updated = place_barrier(board, ACTOR, Position(2, 3), QUOTA)
    assert not is_legal_move(updated, ACTOR, Move.N)
    assert is_legal_move(board, ACTOR, Move.N)  # original untouched


def test_barrier_placement_leaves_the_actor_position_unchanged() -> None:
    actor = Position(3, 3)
    updated = place_barrier(_board(), actor, Position(3, 4), QUOTA)
    assert actor == Position(3, 3)
    assert isinstance(updated, Board)
    # The effect returns only a Board: it structurally cannot move the actor.
    assert not hasattr(updated, "actor")


def test_four_barriers_trap_the_thief_and_score_a_capture() -> None:
    board, police = _board(), Position(2, 3)
    for target in (Position(2, 3), Position(4, 3), Position(3, 2), Position(3, 4)):
        board = place_barrier(board, target, target, QUOTA)
    assert legal_moves(board, ACTOR) == (Move.STAY,)
    assert is_trapped(board, ACTOR)
    outcome = evaluate_terminal(captured=True, step=7, limits=TurnLimits(35, 35))
    assert outcome is Outcome.CAPTURE
    assert score_for(outcome).cop == 20
    assert score_for(outcome).thief == 5
    assert police == Position(2, 3)


def test_barrier_on_the_occupied_cell_is_a_capture_and_scores_it() -> None:
    assert is_barrier_capture(Position(3, 3), ACTOR)
    outcome = evaluate_terminal(captured=True, step=1, limits=TurnLimits(35, 35))
    assert score_for(outcome) == score_for(Outcome.CAPTURE)


def test_survival_terminal_maps_to_the_survival_score() -> None:
    outcome = evaluate_terminal(captured=False, step=35, limits=TurnLimits(35, 35))
    assert outcome is Outcome.SURVIVAL
    assert (score_for(outcome).cop, score_for(outcome).thief) == (5, 10)


def test_multi_turn_scent_trace_is_deterministic() -> None:
    def trace() -> list[str]:
        field = ScentField.zero(_board())
        out = []
        for step in range(4):
            sources = (ACTOR,) if step % 2 == 0 else ()
            field = field.evolve(KERNEL, sources, PARAMS)
            out.append(str(field.at(ACTOR)))
        return out

    first = trace()
    assert first == trace() == trace()
    assert first[0] == "0.9"
    assert Decimal(first[1]) == Decimal("0.81")


def test_quota_cannot_be_bypassed_by_repeated_placement() -> None:
    board = _board()
    quota = BarrierQuota(max_barriers=14)
    placed = 0
    for row in range(GRID):
        for col in range(GRID):
            target = Position(row, col)
            if is_placeable(board, target, target, quota):
                board = place_barrier(board, target, target, quota)
                placed += 1
    assert placed == 14
    assert len(board.blocked) == 14


def _probe(seed: str) -> str:
    env = dict(os.environ, PYTHONHASHSEED=seed)
    run = subprocess.run(
        [sys.executable, "-c", PROBE], capture_output=True, text=True, env=env, check=True
    )
    return run.stdout.strip()


def test_results_are_stable_under_python_hash_randomisation() -> None:
    assert len({_probe(seed) for seed in ("0", "1", "424242")}) == 1


def test_presence_then_departure_scent_trace_is_exact() -> None:
    # C-10: presence holds the cell at the bound; departure decays by (1 - rho).
    field = ScentField.zero(_board()).evolve(KERNEL, (ACTOR,), PARAMS)
    assert field.at(ACTOR) == Decimal("0.9")
    for _ in range(2):
        field = field.evolve(KERNEL, (ACTOR,), PARAMS)
        assert field.at(ACTOR) == Decimal("0.9")
    for expected in ("0.81", "0.729"):
        field = field.evolve(KERNEL, (), PARAMS)
        assert field.at(ACTOR) == Decimal(expected)
