"""Boundary, determinism and layer-boundary tests for the local turn service.

Stage 3C is the LOCAL EFFECT step only. It must not declare a terminal
outcome (capture has precedence and requires verified opponent-public facts,
PRD01-FR-053/055), must not score, and must not evolve scent (Ch 4 p.43 decays
at the end of a **full** turn, after both agents have moved).
"""

import inspect
import os
import subprocess
import sys

import pytest

from mars777_police.app import turn_service
from mars777_police.app.turn_service import (
    ActionsExhaustedError,
    LocalTurnService,
    MoveAction,
)
from mars777_police.domain.barriers import BarrierQuota
from mars777_police.domain.board import Board, Position
from mars777_police.domain.rules import Move
from mars777_police.domain.terminal import TurnLimits
from mars777_police.domain.truth import LocalTruth

GRID = 7
CENTRE = Position(3, 3)
LIMITS = TurnLimits(max_moves=35, survival_threshold=35)
QUOTA = BarrierQuota(max_barriers=14)
PROBE = (
    "from mars777_police.app.turn_service import LocalTurnService, MoveAction;"
    "from mars777_police.domain.barriers import BarrierQuota;"
    "from mars777_police.domain.board import Board, Position;"
    "from mars777_police.domain.rules import Move;"
    "from mars777_police.domain.terminal import TurnLimits;"
    "from mars777_police.domain.truth import LocalTruth;"
    "s=LocalTurnService(limits=TurnLimits(35,35), quota=BarrierQuota(max_barriers=14));"
    "t=LocalTruth(board=Board(rows=7,cols=7), own_position=Position(3,3));"
    "r=s.apply(t, MoveAction(Move.N));"
    "print(r.truth.own_position, r.completed_step, r.kind.value)"
)


def _service() -> LocalTurnService:
    return LocalTurnService(limits=LIMITS, quota=QUOTA)


def _truth(steps: int = 0) -> LocalTruth:
    return LocalTruth(board=Board(rows=GRID, cols=GRID), own_position=CENTRE, completed_steps=steps)


def test_one_action_remains_at_the_penultimate_step() -> None:
    result = _service().apply(_truth(steps=LIMITS.max_moves - 1), MoveAction(Move.STAY))
    assert result.truth.completed_steps == LIMITS.max_moves
    assert result.completed_step == LIMITS.max_moves


def test_the_state_at_the_ceiling_is_valid_but_refuses_another_action() -> None:
    at_ceiling = _truth(steps=LIMITS.max_moves)
    assert at_ceiling.completed_steps == LIMITS.max_moves
    with pytest.raises(ActionsExhaustedError):
        _service().apply(at_ceiling, MoveAction(Move.STAY))


def test_a_state_beyond_the_ceiling_also_refuses() -> None:
    with pytest.raises(ActionsExhaustedError):
        _service().apply(_truth(steps=LIMITS.max_moves + 1), MoveAction(Move.STAY))


def test_exhaustion_is_not_a_game_outcome() -> None:
    message = ""
    try:
        _service().apply(_truth(steps=LIMITS.max_moves), MoveAction(Move.STAY))
    except ActionsExhaustedError as exc:
        message = str(exc).lower()
    for word in ("survival", "capture", "tie", "technical", "score", "win", "lose"):
        assert word not in message


def test_no_terminal_outcome_or_score_is_produced() -> None:
    result = _service().apply(_truth(), MoveAction(Move.N))
    for forbidden in ("outcome", "score", "terminal", "winner", "cop", "thief"):
        assert not hasattr(result, forbidden)
    source = inspect.getsource(turn_service)
    assert "evaluate_terminal" not in source
    assert "score_for" not in source


def test_no_scent_lifecycle_exists_in_the_application_layer() -> None:
    source = inspect.getsource(turn_service)
    for forbidden in ("ScentField", "ScentKernel", "evolve", "scent"):
        assert forbidden not in source
    result = _service().apply(_truth(), MoveAction(Move.N))
    assert not hasattr(result.truth, "scent")


def test_no_opponent_truth_or_transport_in_the_application_layer() -> None:
    source = inspect.getsource(turn_service).lower()
    for forbidden in (
        "opponent",
        "enemy",
        "nonce",
        "commitment",
        "socket",
        "url",
        "fastmcp",
        "llm",
        "gui",
        "gmail",
        "asyncio",
        "referee",
    ):
        assert forbidden not in source


def test_equal_inputs_produce_equal_results() -> None:
    first = _service().apply(_truth(), MoveAction(Move.N))
    second = _service().apply(_truth(), MoveAction(Move.N))
    assert first.truth == second.truth
    assert (first.kind, first.completed_step) == (second.kind, second.completed_step)


def test_results_are_stable_under_python_hash_randomisation() -> None:
    outputs = set()
    for seed in ("0", "1", "424242"):
        run = subprocess.run(
            [sys.executable, "-c", PROBE],
            capture_output=True,
            text=True,
            env=dict(os.environ, PYTHONHASHSEED=seed),
            check=True,
        )
        outputs.add(run.stdout.strip())
    assert len(outputs) == 1


def test_the_application_never_reimplements_domain_rules() -> None:
    source = inspect.getsource(turn_service)
    assert "apply_move" in source
    assert "place_barrier" in source or "BarrierAction" in source
    for reimplementation in ("MOVE_ORDER", "_DELTAS", "ORTHOGONAL_OFFSETS", "is_traversable"):
        assert reimplementation not in source
