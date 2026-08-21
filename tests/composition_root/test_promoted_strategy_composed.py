"""The agent the tournament actually receives carries the promoted policy.

Reading `composition.py` proves the name is wired. This builds a real agent
through the production entry point and asks it to choose, because the object
the tournament gets is what decides the game - not the source text.

Lives beside the other composition tests so the production object graph is built
the same way they build it.
"""

from decimal import Decimal

import composed_builders as build

from mars777_police.app.competitive_strategy import (
    CONSERVATIVE,
    TRAP_BONUS,
    CompetitiveStrategy,
)
from mars777_police.domain.actions import BarrierAction
from mars777_police.domain.barriers import BarrierQuota
from mars777_police.domain.board import Board, Position
from mars777_police.domain.observation import Observation
from mars777_police.domain.scent import ScentField
from mars777_police.domain.scent_belief import ScentBelief


def _view(shape: Board, cell: Position, weights: dict[Position, str]) -> Observation:
    grid = tuple(
        tuple(Decimal(weights.get(Position(r, c), "0")) for c in range(shape.cols))
        for r in range(shape.rows)
    )
    return Observation(
        board=shape,
        own_position=cell,
        quota=BarrierQuota(14),
        scent=ScentBelief(ScentField(shape.rows, shape.cols, 0, grid), 1),
    )


def test_the_composed_agent_is_the_promoted_policy() -> None:
    composed = build.compose()

    assert isinstance(composed.strategy, CompetitiveStrategy)
    assert type(composed.strategy.baseline).__name__ == "BaselineStrategy"


def test_the_composed_agent_places_on_the_promoted_rule() -> None:
    """No research flag and no environment switch selects this behaviour."""
    composed = build.compose()
    shape = Board(rows=5, cols=5)

    chosen = composed.strategy.choose_action(_view(shape, Position(2, 2), {Position(1, 2): "0.9"}))

    assert chosen == BarrierAction(Position(1, 2))


def test_the_composed_agent_carries_the_frozen_parameters() -> None:
    build.compose()

    assert Decimal("0.9") == CONSERVATIVE
    assert Decimal(10) == TRAP_BONUS
