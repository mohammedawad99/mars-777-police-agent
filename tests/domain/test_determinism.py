"""Determinism tests for the Stage-3A domain foundation.

Covers PRD-01 §19 (no dependence on unordered iteration or on Python hash
randomization) and §21 (identical results on Linux and Windows). Integer
arithmetic only; no clock, no randomness, no I/O in the domain.
"""

import os
import subprocess
import sys

from mars777_police.domain.board import Board, Position
from mars777_police.domain.config_model import GridConfig
from mars777_police.domain.rules import MOVE_ORDER, Move, apply_move, legal_moves

GRID = 7
CENTRE = Position(3, 3)
WALLS = (Position(2, 3), Position(3, 2), Position(4, 3))

PROBE = (
    "from mars777_police.domain.board import Board, Position;"
    "from mars777_police.domain.rules import legal_moves;"
    "cells=[Position(2,3),Position(3,2),Position(4,3)];"
    "b=Board(rows=7,cols=7,blocked=frozenset(cells));"
    "print([m.value for m in legal_moves(b, Position(3,3))])"
)


def test_move_order_is_an_ordered_sequence_not_a_set() -> None:
    assert isinstance(MOVE_ORDER, tuple)
    assert not isinstance(MOVE_ORDER, frozenset | set)


def test_legal_moves_is_independent_of_blocked_insertion_order() -> None:
    orders = (
        WALLS,
        tuple(reversed(WALLS)),
        (WALLS[1], WALLS[2], WALLS[0]),
        (WALLS[2], WALLS[0], WALLS[1]),
    )
    results = {
        legal_moves(Board(rows=GRID, cols=GRID, blocked=frozenset(order)), CENTRE)
        for order in orders
    }
    assert len(results) == 1
    assert results.pop() == (Move.E, Move.STAY)


def test_equal_inputs_produce_equal_outputs() -> None:
    board_a = Board(rows=GRID, cols=GRID, blocked=frozenset(WALLS))
    board_b = Board(rows=GRID, cols=GRID, blocked=frozenset(reversed(WALLS)))
    assert board_a == board_b
    assert legal_moves(board_a, CENTRE) == legal_moves(board_b, CENTRE)
    assert apply_move(board_a, CENTRE, Move.E) == apply_move(board_b, CENTRE, Move.E)


def test_repeated_calls_are_stable() -> None:
    board = GridConfig(rows=GRID, cols=GRID).to_board(WALLS)
    first = legal_moves(board, CENTRE)
    for _ in range(5):
        assert legal_moves(board, CENTRE) == first


def test_config_built_board_matches_a_directly_built_board() -> None:
    from_config = GridConfig(rows=GRID, cols=GRID).to_board(WALLS)
    direct = Board(rows=GRID, cols=GRID, blocked=frozenset(WALLS))
    assert from_config == direct


def test_ordering_survives_python_hash_randomization() -> None:
    outputs = set()
    for seed in ("0", "1", "424242"):
        env = dict(os.environ, PYTHONHASHSEED=seed)
        # Fixed argv, no shell: a local probe of this package only.
        completed = subprocess.run(
            [sys.executable, "-c", PROBE],
            capture_output=True,
            text=True,
            env=env,
            check=True,
        )
        outputs.add(completed.stdout.strip())
    assert len(outputs) == 1
    assert outputs.pop() == "['E', 'STAY']"
