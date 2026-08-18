"""Scent reaching a decision - as a tie-break, and only as a tie-break.

Ch 10 §10.3.3 put a *blind* baseline at the previous stage, *"blind in the sense
that there is not yet scent, natural language or deception"*. This is the stage
that ends the blindness, and the smallest honest way to do it is to let scent
decide only what the existing objective leaves undecided.

**Police follows the stronger evidence.** The thief's emissions are legal
partial evidence of where it has been, so on an otherwise equal choice the
pursuer prefers the cell where that evidence is strongest. It is a
PROJECT-DERIVED tie-break, not a source mandate and not a claim of optimality:
the accessibility objective is untouched and still decides every case it can.

**Nothing else moves.** With no evidence, or with evidence equal on both
candidates, the ordering is exactly what it was before this stage - which is
what the regression corpus below exists to prove.
"""

from decimal import Decimal

import pytest

from mars777_police.app.baseline_strategy import BaselineStrategy
from mars777_police.domain.actions import MoveAction
from mars777_police.domain.barriers import BarrierQuota
from mars777_police.domain.board import Board, Position
from mars777_police.domain.observation import Observation
from mars777_police.domain.rules import Move, destination_of, legal_moves
from mars777_police.domain.scent import ScentField
from mars777_police.domain.scent_belief import ScentBelief

QUOTA = BarrierQuota(14)
ZERO = Decimal("0")


def board(rows: int = 5, cols: int = 5, blocked: frozenset[Position] = frozenset()) -> Board:
    return Board(rows=rows, cols=cols, blocked=blocked)


def belief_at(shape: Board, weights: dict[Position, str]) -> ScentBelief:
    """A belief whose field carries exactly the intensities a test names."""
    grid = tuple(
        tuple(Decimal(weights.get(Position(r, c), "0")) for c in range(shape.cols))
        for r in range(shape.rows)
    )
    return ScentBelief(ScentField(shape.rows, shape.cols, 0, grid), 1)


def seen(shape: Board, cell: Position, scent: ScentBelief) -> Observation:
    return Observation(board=shape, own_position=cell, quota=QUOTA, scent=scent)


def tied_candidates(shape: Board, cell: Position, strategy: BaselineStrategy) -> list[Move]:
    """The moves the pre-scent objective cannot separate from *cell*."""
    scores = {
        move: strategy._spread(seen(shape, cell, ScentBelief()), move)
        for move in legal_moves(shape, cell)
    }
    best = min(scores.values())
    return [move for move, score in scores.items() if score == best]


TIE_CELL = Position(0, 0)
"""A corner of the open board, where the accessibility score genuinely ties.

Chosen by measurement, not by assumption: from the centre the objective already
prefers one candidate outright, so a "tie-break" test there would pass without
the tie-break existing. From the corner two real moves score identically.
"""


def test_the_fixture_leaves_a_real_tie_to_break() -> None:
    """The fixture itself must be honest: without a tie there is nothing to prove."""
    assert len(tied_candidates(board(), TIE_CELL, BaselineStrategy())) >= 2


def test_police_prefers_the_higher_scent_destination_on_a_tie() -> None:
    shape, cell, strategy = board(), TIE_CELL, BaselineStrategy()
    tied = tied_candidates(shape, cell, strategy)
    favoured = destination_of(cell, tied[-1])

    chosen = strategy.choose_action(seen(shape, cell, belief_at(shape, {favoured: "0.9"})))

    assert chosen == MoveAction(tied[-1])


@pytest.mark.parametrize("index", [0, 1])
def test_any_tied_destination_can_win_by_carrying_the_evidence(index: int) -> None:
    """Not an accident of ordering: whichever cell holds the scent is chosen."""
    shape, cell, strategy = board(), TIE_CELL, BaselineStrategy()
    tied = tied_candidates(shape, cell, strategy)
    favoured = destination_of(cell, tied[index])

    chosen = strategy.choose_action(seen(shape, cell, belief_at(shape, {favoured: "0.5"})))

    assert chosen == MoveAction(tied[index])


def test_equal_scent_leaves_the_old_deterministic_tie_break_in_charge() -> None:
    shape, cell, strategy = board(), TIE_CELL, BaselineStrategy()
    blind = strategy.choose_action(seen(shape, cell, ScentBelief()))
    even = {destination_of(cell, move): "0.4" for move in legal_moves(shape, cell)}

    assert strategy.choose_action(seen(shape, cell, belief_at(shape, even))) == blind


CORPUS = (
    (board(), Position(0, 0)),
    (board(), Position(2, 2)),
    (board(), Position(4, 4)),
    (board(3, 3), Position(1, 1)),
    (board(5, 5, frozenset({Position(1, 1), Position(3, 3)})), Position(2, 2)),
    (board(4, 6), Position(1, 3)),
)


@pytest.mark.parametrize(("shape", "cell"), CORPUS)
def test_no_evidence_reproduces_the_pre_scent_decision(shape: Board, cell: Position) -> None:
    """AC: a neutral belief must not move a single existing decision."""
    strategy = BaselineStrategy()
    expected = MoveAction(
        min(
            legal_moves(shape, cell),
            key=lambda m: strategy._spread(seen(shape, cell, ScentBelief()), m),
        )
    )

    assert strategy.choose_action(seen(shape, cell, ScentBelief())) == expected


def test_scent_never_makes_an_illegal_destination_selectable() -> None:
    """A wall soaked in evidence is still a wall: legality is not a preference."""
    walls = frozenset({Position(1, 2)})
    shape, cell, strategy = board(5, 5, walls), Position(2, 2), BaselineStrategy()
    drenched = belief_at(shape, {Position(1, 2): "0.9"})

    chosen = strategy.choose_action(seen(shape, cell, drenched))

    assert isinstance(chosen, MoveAction)
    assert chosen.move in legal_moves(shape, cell)
    assert destination_of(cell, chosen.move) != Position(1, 2)


def test_the_objective_still_outranks_the_evidence() -> None:
    """Scent breaks ties; it does not overrule the accessibility comparison."""
    shape, cell, strategy = (
        board(5, 5, frozenset({Position(0, 1), Position(1, 0)})),
        Position(1, 1),
        BaselineStrategy(),
    )
    scores = {
        m: strategy._spread(seen(shape, cell, ScentBelief()), m) for m in legal_moves(shape, cell)
    }
    worst = max(scores, key=lambda m: scores[m])

    if scores[worst] != min(scores.values()):
        chosen = strategy.choose_action(
            seen(shape, cell, belief_at(shape, {destination_of(cell, worst): "0.9"}))
        )
        assert chosen != MoveAction(worst)
