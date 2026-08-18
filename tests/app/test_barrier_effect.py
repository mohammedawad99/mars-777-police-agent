"""Which cells a lawful placement would newly corner, and no trap physics at all.

`GAME-005` belongs to `domain.terminal.is_trapped` and the placement rule to
`domain.barriers`; this helper only asks both of them a question about a board
that does not exist yet. Restating either would give the game two answers.

A cell that was already trapped before the placement is not *newly* trapped, and
the blocked target itself is not a trapped traversable cell - it is a wall. Both
distinctions matter to a policy that will spend an irreversible quota on them.
"""

from mars777_police.domain.barrier_effect import newly_trapped
from mars777_police.domain.barriers import BarrierQuota
from mars777_police.domain.board import Board, Position

QUOTA = BarrierQuota(14)


def board(blocked: frozenset[Position] = frozenset()) -> Board:
    return Board(rows=5, cols=5, blocked=blocked)


def test_a_placement_that_corners_nobody_reports_nothing() -> None:
    assert newly_trapped(board(), Position(2, 2), Position(2, 3), QUOTA) == ()


def test_the_blocked_target_is_never_itself_a_trapped_cell() -> None:
    """A wall is not a cornered actor, however surrounded it looks."""
    walls = frozenset({Position(0, 1), Position(1, 0)})
    trapped = newly_trapped(board(walls), Position(1, 1), Position(1, 1), QUOTA)

    assert Position(1, 1) not in trapped


def test_closing_the_last_exit_of_a_corner_is_newly_trapped() -> None:
    """`(0,0)` has exactly two exits; blocking the second corners that cell."""
    walls = frozenset({Position(0, 1)})
    trapped = newly_trapped(board(walls), Position(1, 1), Position(1, 0), QUOTA)

    assert Position(0, 0) in trapped


def test_a_cell_already_trapped_before_is_not_newly_trapped() -> None:
    walls = frozenset({Position(0, 1), Position(1, 0)})
    shape = board(walls)

    assert newly_trapped(shape, Position(2, 2), Position(2, 3), QUOTA) == ()


def test_the_result_is_ordered_deterministically() -> None:
    """Row then column, so two runs cannot disagree about which cell is first."""
    walls = frozenset({Position(0, 1), Position(1, 0), Position(0, 3), Position(1, 4)})
    trapped = newly_trapped(board(walls), Position(0, 2), Position(0, 2), QUOTA)

    assert list(trapped) == sorted(trapped, key=lambda cell: (cell.row, cell.col))


def test_an_illegal_placement_has_no_effect_to_describe() -> None:
    """The legality authority answers first; this helper never invents a board."""
    assert newly_trapped(board(), Position(0, 0), Position(4, 4), QUOTA) == ()
    assert (
        newly_trapped(board(frozenset({Position(0, 1)})), Position(0, 0), Position(0, 1), QUOTA)
        == ()
    )
