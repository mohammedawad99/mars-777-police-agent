"""The police policy that may spend a barrier when the evidence supports one.

Ch 6 §6.3.1 leaves the movement policy to the group, and BAR-004 gives the
police an action the baseline never used: forgo the move and place a barrier.
Two lawful routes make that competitively meaningful - BAR-003 captures a thief
standing on the target, and GAME-005 captures one left with no traversable
neighbour - and neither needs a `CaptureClaim`, so neither can produce the
`FALSE_CAPTURE_CLAIM` technical loss that a belief-based declaration would risk.

**The barrier must earn the turn.** Movement is what the frozen baseline
decides, and a placement displaces it only when the lawful scent evidence
supporting the placement is *strictly stronger* than the evidence at the cell
the baseline would have moved to. With no evidence, uniform evidence, or merely
equal evidence, this policy is the baseline exactly - which is what makes it
safe to ship and what the regression corpus below pins.

Nothing here claims the thief occupies anything. Support is belief.
"""

from decimal import Decimal

import pytest

from mars777_police.app.baseline_strategy import BaselineStrategy
from mars777_police.app.competitive_strategy import CompetitiveStrategy, Support
from mars777_police.domain.actions import BarrierAction, MoveAction
from mars777_police.domain.barriers import BarrierQuota, is_placeable
from mars777_police.domain.board import Board, Position
from mars777_police.domain.observation import Observation
from mars777_police.domain.rules import destination_of, legal_moves
from mars777_police.domain.scent import ScentField
from mars777_police.domain.scent_belief import ScentBelief

QUOTA = BarrierQuota(14)
ZERO = Decimal("0")
BASELINE = BaselineStrategy()
COMPETITIVE = CompetitiveStrategy()


def board(rows: int = 5, cols: int = 5, blocked: frozenset[Position] = frozenset()) -> Board:
    return Board(rows=rows, cols=cols, blocked=blocked)


def belief(shape: Board, weights: dict[Position, str]) -> ScentBelief:
    grid = tuple(
        tuple(Decimal(weights.get(Position(r, c), "0")) for c in range(shape.cols))
        for r in range(shape.rows)
    )
    return ScentBelief(ScentField(shape.rows, shape.cols, 0, grid), 1)


def seen(
    shape: Board, cell: Position, scent: ScentBelief, quota: BarrierQuota = QUOTA
) -> Observation:
    return Observation(board=shape, own_position=cell, quota=quota, scent=scent)


def baseline_landing(view: Observation) -> Position:
    chosen = BASELINE.choose_action(view)
    assert isinstance(chosen, MoveAction)
    return destination_of(view.own_position, chosen.move)


# ---------------------------------------------------------------- safety


def test_no_evidence_is_exactly_the_baseline_decision() -> None:
    for cell in (Position(0, 0), Position(2, 2), Position(4, 4), Position(1, 3)):
        view = seen(board(), cell, ScentBelief())
        assert COMPETITIVE.choose_action(view) == BASELINE.choose_action(view)


def test_uniform_evidence_is_exactly_the_baseline_decision() -> None:
    """Nothing is *strictly* stronger than anything, so nothing displaces a move."""
    shape, cell = board(), Position(2, 2)
    everywhere = {Position(r, c): "0.5" for r in range(5) for c in range(5)}
    view = seen(shape, cell, belief(shape, everywhere))

    assert COMPETITIVE.choose_action(view) == BASELINE.choose_action(view)


def test_support_equal_to_the_moves_support_still_moves() -> None:
    shape, cell = board(), Position(2, 2)
    view_blind = seen(shape, cell, ScentBelief())
    landing = baseline_landing(view_blind)
    view = seen(shape, cell, belief(shape, {landing: "0.6", Position(2, 3): "0.6"}))

    assert isinstance(COMPETITIVE.choose_action(view), MoveAction)


def test_an_exhausted_quota_leaves_only_movement() -> None:
    """`is_placeable` counts the public board against the quota; nothing is left."""
    walls = frozenset(
        {Position(0, c) for c in range(5)}
        | {Position(4, c) for c in range(5)}
        | {Position(2, 4), Position(1, 4), Position(3, 4), Position(1, 0)}
    )
    tight = BarrierQuota(14)
    shape, cell = board(blocked=walls), Position(2, 2)
    assert len(shape.blocked) >= tight.max_barriers
    view = seen(shape, cell, belief(shape, {Position(2, 3): "0.9"}), quota=tight)

    assert isinstance(COMPETITIVE.choose_action(view), MoveAction)


def test_a_blocked_target_is_never_returned() -> None:
    walls = frozenset({Position(2, 3)})
    shape, cell = board(blocked=walls), Position(2, 2)
    view = seen(shape, cell, belief(shape, {Position(2, 3): "0.9"}))

    chosen = COMPETITIVE.choose_action(view)
    if isinstance(chosen, BarrierAction):
        assert chosen.target != Position(2, 3)


def test_an_off_board_high_scent_cell_cannot_be_selected() -> None:
    shape, cell = board(), Position(0, 0)
    view = seen(shape, cell, belief(shape, {Position(0, 1): "0.9"}))

    chosen = COMPETITIVE.choose_action(view)
    if isinstance(chosen, BarrierAction):
        assert shape.contains(chosen.target)


def test_the_actors_own_cell_is_never_a_competitive_target() -> None:
    """Legal under BAR-004, but blocking ourselves is not this policy."""
    shape, cell = board(), Position(2, 2)
    view = seen(shape, cell, belief(shape, {cell: "0.9"}))

    chosen = COMPETITIVE.choose_action(view)
    assert not (isinstance(chosen, BarrierAction) and chosen.target == cell)


def test_every_returned_barrier_satisfies_the_placement_authority() -> None:
    shape, cell = board(), Position(2, 2)
    for target in (Position(1, 2), Position(3, 2), Position(2, 1), Position(2, 3)):
        view = seen(shape, cell, belief(shape, {target: "0.9"}))
        chosen = COMPETITIVE.choose_action(view)
        if isinstance(chosen, BarrierAction):
            assert is_placeable(shape, cell, chosen.target, QUOTA)


def test_a_returned_move_is_always_a_legal_move() -> None:
    shape, cell = board(), Position(2, 2)
    view = seen(shape, cell, belief(shape, {Position(4, 4): "0.9"}))
    chosen = COMPETITIVE.choose_action(view)

    if isinstance(chosen, MoveAction):
        assert chosen.move in legal_moves(shape, cell)


def test_the_policy_never_produces_a_capture_claim() -> None:
    """A `PhysicalAction` cannot carry one - pinned so it stays that way."""
    shape, cell = board(), Position(2, 2)
    chosen = COMPETITIVE.choose_action(seen(shape, cell, belief(shape, {Position(2, 3): "0.9"})))

    assert not hasattr(chosen, "claim")
    assert isinstance(chosen, MoveAction | BarrierAction)


def test_the_decision_is_deterministic() -> None:
    shape, cell = board(), Position(2, 2)
    view = seen(shape, cell, belief(shape, {Position(2, 3): "0.9"}))

    assert COMPETITIVE.choose_action(view) == COMPETITIVE.choose_action(view)


# ---------------------------------------------------------------- admission


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


def test_the_strategy_satisfies_the_unchanged_port() -> None:
    """Structurally, because `StrategyPort` is deliberately not runtime-checkable."""
    import inspect

    from mars777_police.app.strategy_api import StrategyPort

    port = inspect.signature(StrategyPort.choose_action)
    mine = inspect.signature(CompetitiveStrategy.choose_action)

    assert list(mine.parameters) == list(port.parameters)
    assert mine.return_annotation == port.return_annotation
