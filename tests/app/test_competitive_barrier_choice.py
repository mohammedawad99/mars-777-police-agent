"""Which cell the barrier goes on, and what settles it when two cells tie.

Rewritten at Stage 9B-2, when the barrier rule was replaced by the revision the
final holdout judged. The old rule scored a placement by its single strongest
route and admitted it only when that beat the cell the mover was stepping onto;
the promoted rule scores an **expectation over the whole lawful belief** and
admits on an absolute floor. These pin the new ordering just as tightly: value
first, then row, then column - deterministic all the way down, because a
strategy that broke ties by chance could not be replayed.
"""

from decimal import Decimal

from test_competitive_strategy import belief, board, seen

from mars777_police.app.competitive_strategy import (
    CONSERVATIVE,
    CompetitiveStrategy,
    believed_cells,
)
from mars777_police.domain.actions import BarrierAction, MoveAction
from mars777_police.domain.board import Position

COMPETITIVE = CompetitiveStrategy()


def test_direct_evidence_on_the_target_admits_a_barrier_with_no_trap_at_all() -> None:
    """Case A: a full source emission next door clears the floor by itself."""
    shape, cell = board(), Position(2, 2)
    view = seen(shape, cell, belief(shape, {Position(1, 2): "0.9"}))

    assert COMPETITIVE.choose_action(view) == BarrierAction(Position(1, 2))


def test_a_hot_landing_cell_no_longer_suppresses_the_placement() -> None:
    """The measured defect the promotion fixed.

    The evidence sits on the cell the mover is standing next to *and* on a
    lawful target. Under the old strictly-greater gate this was refused; the
    promoted floor does not consult the landing cell at all.
    """
    shape, cell = board(), Position(2, 2)
    view = seen(shape, cell, belief(shape, {Position(1, 2): "0.9", Position(2, 2): "0.9"}))

    assert isinstance(COMPETITIVE.choose_action(view), BarrierAction)


def test_trap_evidence_can_admit_a_barrier_whose_own_cell_is_quiet() -> None:
    """Case B: the evidence sits on the cell the placement would corner."""
    walls = frozenset({Position(0, 1)})
    shape, cell = board(blocked=walls), Position(1, 1)
    view = seen(shape, cell, belief(shape, {Position(0, 0): "0.9"}))

    assert COMPETITIVE.choose_action(view) == BarrierAction(Position(1, 0))


def test_cornering_weak_evidence_outranks_adjoining_strong_evidence() -> None:
    """Case C: `TRAP_BONUS` is what makes an ending worth more than a nudge."""
    shape, cell = board(blocked=frozenset({Position(1, 0)})), Position(0, 2)
    view = seen(shape, cell, belief(shape, {Position(0, 0): "0.1", Position(0, 4): "0.8"}))
    mass = believed_cells(view)

    assert COMPETITIVE._value(view, mass, Position(0, 1)) == Decimal(1)
    assert COMPETITIVE._value(view, mass, Position(0, 3)) == Decimal("0.8")
    assert COMPETITIVE.choose_action(view) == BarrierAction(Position(0, 1))


def test_row_then_column_settles_a_complete_tie() -> None:
    """Case D: identical value on two targets is decided by cell order."""
    shape, cell = board(), Position(2, 2)
    view = seen(shape, cell, belief(shape, {Position(1, 2): "0.9", Position(3, 2): "0.9"}))
    mass = believed_cells(view)

    assert COMPETITIVE._value(view, mass, Position(1, 2)) == COMPETITIVE._value(
        view, mass, Position(3, 2)
    )
    assert COMPETITIVE.choose_action(view) == BarrierAction(Position(1, 2))


def test_the_floor_is_absolute_and_weak_evidence_never_buys_a_barrier() -> None:
    """Admission is now about clearing 0.9, not about beating the landing cell."""
    shape, cell = board(), Position(2, 2)

    for weight in ("0.1", "0.4", "0.8"):
        view = seen(shape, cell, belief(shape, {Position(1, 2): weight}))
        mass = believed_cells(view)

        assert COMPETITIVE._value(view, mass, Position(1, 2)) < CONSERVATIVE
        assert isinstance(COMPETITIVE.choose_action(view), MoveAction)


def test_evidence_exactly_at_the_floor_admits() -> None:
    """The comparison is `>=`, and that is load-bearing rather than incidental.

    The domain caps a single cell at **0.9** (Appendix F Table 16, FIXED), so a
    lone cell of direct evidence can only ever *equal* the floor, never exceed
    it. A strictly-greater comparison would make single-source evidence unable
    to fund a barrier at all.
    """
    shape, cell = board(), Position(2, 2)
    view = seen(shape, cell, belief(shape, {Position(1, 2): "0.9"}))
    mass = believed_cells(view)

    assert COMPETITIVE._value(view, mass, Position(1, 2)) == CONSERVATIVE
    assert COMPETITIVE.choose_action(view) == BarrierAction(Position(1, 2))


def test_adjacent_evidence_accumulates_rather_than_taking_the_maximum() -> None:
    """The promoted score is an expectation, and this is where it differs most."""
    shape, cell = board(), Position(2, 2)
    view = seen(shape, cell, belief(shape, {Position(1, 1): "0.5", Position(0, 2): "0.5"}))
    mass = believed_cells(view)

    assert COMPETITIVE._value(view, mass, Position(1, 2)) == Decimal("1.0")
    assert COMPETITIVE.choose_action(view) == BarrierAction(Position(1, 2))
