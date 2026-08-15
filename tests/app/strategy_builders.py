"""Boards a baseline decision can be reasoned about by hand.

Deliberately tiny and literal: a strategy test that builds its board through a
helper with rules in it would be testing the helper. Everything here composes
`Board`, `Position` and `Observation` directly, so a failing assertion points at
the policy rather than at a fixture that quietly did the thinking.
"""

from mars777_police.domain.barriers import BarrierQuota
from mars777_police.domain.board import Board, Position
from mars777_police.domain.observation import Observation
from mars777_police.domain.rules import Move, destination_of
from mars777_police.domain.terminal import TurnLimits

GRID = 7
QUOTA = BarrierQuota(14)
LIMITS = TurnLimits(max_moves=35, survival_threshold=35)
CENTRE = Position(3, 3)


def board(*blocked: Position) -> Board:
    """A locked-default 7x7 grid carrying exactly the barriers named."""
    return Board(rows=GRID, cols=GRID, blocked=frozenset(blocked))


def seen(own: Position, *blocked: Position) -> Observation:
    """What an agent standing on *own* may legally see of that board."""
    return Observation(board=board(*blocked), own_position=own, quota=QUOTA)


def column(col: int, *rows: int) -> tuple[Position, ...]:
    """A vertical run of barriers, for building walls and pockets."""
    return tuple(Position(row, col) for row in rows)


def cells(one: Board) -> tuple[Position, ...]:
    """Every cell of *one*, in a fixed row-major order."""
    return tuple(Position(row, col) for row in range(one.rows) for col in range(one.cols))


def manhattan_spread(one: Board, origin: Position) -> int:
    """The barrier-blind spread a Manhattan shortcut would have scored.

    Present only so a test can prove the policy did **not** compute this: it
    ignores every barrier, which is exactly the defect `PRD03-FR-014` forbids.
    """
    return sum(
        abs(origin.row - cell.row) + abs(origin.col - cell.col)
        for cell in cells(one)
        if one.is_traversable(cell)
    )


def destination(observation: Observation, move: Move) -> Position:
    """Where *move* would put the observer, through the domain's own rule."""
    return destination_of(observation.own_position, move)
