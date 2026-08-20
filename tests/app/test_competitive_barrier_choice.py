"""Which cell the barrier goes on, and what settles it when two cells tie.

The policy displaces the baseline's move only when the evidence for a placement
is **strictly** stronger than the evidence where the baseline would have gone.
These pin the whole ordering: direct support, then trap support, then how many
cells the placement newly traps, then row and column - deterministic all the way
down, because a strategy that broke ties by chance could not be replayed.
"""

from decimal import Decimal

import pytest
from test_competitive_strategy import baseline_landing, belief, board, seen

from mars777_police.app.competitive_strategy import CompetitiveStrategy, Support
from mars777_police.domain.actions import BarrierAction
from mars777_police.domain.board import Position
from mars777_police.domain.scent_belief import ScentBelief

COMPETITIVE = CompetitiveStrategy()


def test_direct_support_admits_a_barrier_with_no_trap_at_all() -> None:
    """Case A: strong evidence on an adjacent cell is enough on its own."""
    shape, cell = board(), Position(2, 2)
    view_blind = seen(shape, cell, ScentBelief())
    landing = baseline_landing(view_blind)
    target = next(
        t for t in (Position(1, 2), Position(3, 2), Position(2, 1), Position(2, 3)) if t != landing
    )
    view = seen(shape, cell, belief(shape, {target: "0.9"}))

    chosen = COMPETITIVE.choose_action(view)

    assert chosen == BarrierAction(target)


def test_trap_support_can_admit_a_barrier_whose_own_cell_is_quiet() -> None:
    """Case B: the evidence sits on the cell the placement would corner."""
    walls = frozenset({Position(0, 1)})
    shape, cell = board(blocked=walls), Position(1, 1)
    view = seen(shape, cell, belief(shape, {Position(0, 0): "0.9"}))

    chosen = COMPETITIVE.choose_action(view)

    assert chosen == BarrierAction(Position(1, 0))


def test_higher_trap_support_wins_when_total_support_ties() -> None:
    """Case C: equal `support`, but one target earns it by cornering evidence.

    The tie is asserted mechanically rather than assumed: `(2,1)` carries its
    0.9 through the cell it would corner and `(2,3)` carries the same 0.9
    directly, so only key 2 can separate them.
    """
    walls = frozenset({Position(1, 0), Position(3, 0)})
    shape, cell = board(blocked=walls), Position(2, 2)
    scent = belief(shape, {Position(2, 0): "0.9", Position(2, 3): "0.9"})
    view = seen(shape, cell, scent)

    cornering = COMPETITIVE._support(view, Position(2, 1))
    direct = COMPETITIVE._support(view, Position(2, 3))
    assert cornering.total == direct.total
    assert cornering.trap > direct.trap

    assert COMPETITIVE.choose_action(view) == BarrierAction(Position(2, 1))


def test_more_newly_trapped_cells_wins_when_support_and_trap_tie() -> None:
    """Case D: keys 1 and 2 are exhausted, so the count of cornered cells decides."""
    one = Support(Decimal("0.9"), Decimal("0.9"), 1, Decimal("0"), Position(0, 0))
    two = Support(Decimal("0.9"), Decimal("0.9"), 2, Decimal("0"), Position(4, 4))

    assert min((one, two), key=Support.order) is two


def test_direct_support_then_cell_order_settle_what_remains() -> None:
    """Case E: the last two keys, in order, with everything above them tied."""
    quiet = Support(Decimal("0.9"), Decimal("0.9"), 1, Decimal("0"), Position(0, 0))
    loud = Support(Decimal("0.9"), Decimal("0.9"), 1, Decimal("0.5"), Position(4, 4))
    assert min((quiet, loud), key=Support.order) is loud

    first = Support(Decimal("0.9"), Decimal("0"), 0, Decimal("0.9"), Position(1, 2))
    later = Support(Decimal("0.9"), Decimal("0"), 0, Decimal("0.9"), Position(3, 2))
    assert min((first, later), key=Support.order) is first


def test_row_then_column_settles_a_complete_tie() -> None:
    """Case E: identical evidence on two targets is decided by cell order."""
    shape, cell = board(), Position(2, 2)
    scent = belief(shape, {Position(1, 2): "0.9", Position(3, 2): "0.9"})

    chosen = COMPETITIVE.choose_action(seen(shape, cell, scent))

    assert chosen == BarrierAction(Position(1, 2))


@pytest.mark.parametrize("weight", ["0.1", "0.4", "0.9"])
def test_any_positive_strictly_stronger_support_admits(weight: str) -> None:
    """Admission is about being strictly stronger, not about being large."""
    shape, cell = board(), Position(2, 2)
    view_blind = seen(shape, cell, ScentBelief())
    landing = baseline_landing(view_blind)
    target = next(
        t for t in (Position(1, 2), Position(3, 2), Position(2, 1), Position(2, 3)) if t != landing
    )

    chosen = COMPETITIVE.choose_action(seen(shape, cell, belief(shape, {target: weight})))

    assert chosen == BarrierAction(target)
