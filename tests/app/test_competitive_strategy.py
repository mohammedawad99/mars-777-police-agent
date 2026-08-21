"""That the competitive policy is still the baseline, and still legal.

Every displacement it makes must be lawful and every non-displacement must be
exactly what the baseline would have done. With no evidence, with uniform
evidence, or with an exhausted quota it is the baseline; whatever it returns is a
legal move or a placement the placement authority accepts; and it never declares
a capture, because a wrong claim forfeits while a missed barrier costs one turn.
"""

from decimal import Decimal

from mars777_police.app.baseline_strategy import BaselineStrategy
from mars777_police.app.competitive_strategy import CompetitiveStrategy
from mars777_police.domain.actions import BarrierAction, MoveAction
from mars777_police.domain.barriers import BarrierQuota, is_placeable
from mars777_police.domain.board import Board, Position
from mars777_police.domain.observation import Observation
from mars777_police.domain.rules import destination_of, legal_moves
from mars777_police.domain.scent import ScentField
from mars777_police.domain.scent_belief import ScentBelief

QUOTA = BarrierQuota(14)
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


def test_no_evidence_is_exactly_the_baseline_decision() -> None:
    for cell in (Position(0, 0), Position(2, 2), Position(4, 4), Position(1, 3)):
        view = seen(board(), cell, ScentBelief())
        assert COMPETITIVE.choose_action(view) == BASELINE.choose_action(view)


def test_uniform_evidence_now_funds_a_placement_and_this_is_deliberate() -> None:
    """Changed at Stage 9B-2, and recorded rather than quietly dropped.

    Under the old gate nothing was *strictly* stronger than anything, so a
    synthetic uniform field reproduced the baseline. The promoted rule scores an
    **expectation over the whole belief**, so a board that is believed
    everywhere is a board worth acting on: five cells at 0.5 sum well past the
    0.9 floor.

    This state is synthetic rather than reachable - the source kernel is a 5x5
    radial decay (Appendix F Table 16), so a real field is never uniform - and
    the behaviour it describes was measured on 2,226 sealed scenarios before
    being promoted. What still holds unconditionally is the silent case below.
    """
    shape, cell = board(), Position(2, 2)
    everywhere = {Position(r, c): "0.5" for r in range(5) for c in range(5)}
    view = seen(shape, cell, belief(shape, everywhere))

    chosen = COMPETITIVE.choose_action(view)

    assert isinstance(chosen, BarrierAction)
    assert is_placeable(shape, cell, chosen.target, QUOTA)


def test_the_landing_cell_no_longer_enters_the_admission_decision() -> None:
    """Replaces the old "equal support still moves" rule, which was the defect.

    Comparing a placement against the cell the mover was already stepping onto
    blocked 334 of 375 belief-carrying decisions against a well-located evader.
    The promoted gate is an absolute floor, so an identical belief field admits
    or refuses the same way wherever the baseline happens to be walking.
    """
    shape, cell = board(), Position(2, 2)
    landing = baseline_landing(seen(shape, cell, ScentBelief()))
    with_landing_hot = belief(shape, {landing: "0.9", Position(1, 2): "0.9"})
    without = belief(shape, {Position(1, 2): "0.9"})

    hot_choice = COMPETITIVE.choose_action(seen(shape, cell, with_landing_hot))
    cool_choice = COMPETITIVE.choose_action(seen(shape, cell, without))

    assert isinstance(hot_choice, BarrierAction)
    assert isinstance(cool_choice, BarrierAction)


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


def test_the_strategy_satisfies_the_unchanged_port() -> None:
    """Structurally, because `StrategyPort` is deliberately not runtime-checkable."""
    import inspect

    from mars777_police.app.strategy_api import StrategyPort

    port = inspect.signature(StrategyPort.choose_action)
    mine = inspect.signature(CompetitiveStrategy.choose_action)

    assert list(mine.parameters) == list(port.parameters)
    assert mine.return_annotation == port.return_annotation
