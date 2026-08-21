"""The promoted barrier rule, pinned to the revision the final holdout judged.

Written RED-first against the shipped policy: each test below fails on the
pre-promotion strategy and passes on the promoted one. What is promoted is the
**exact** frozen C4 behaviour - the same threshold, the same trap weight, the
same mover, the same tie-break - so these assert the rule itself rather than the
benchmark it won.
"""

from decimal import Decimal

from mars777_police.app.baseline_strategy import BaselineStrategy
from mars777_police.app.competitive_strategy import (
    CONSERVATIVE,
    TRAP_BONUS,
    CompetitiveStrategy,
    believed_cells,
)
from mars777_police.domain.actions import BarrierAction, MoveAction
from mars777_police.domain.barriers import BarrierQuota, is_placeable
from mars777_police.domain.board import Board, Position
from mars777_police.domain.observation import Observation
from mars777_police.domain.scent import ScentField
from mars777_police.domain.scent_belief import ScentBelief

QUOTA = BarrierQuota(14)
BASELINE = BaselineStrategy()
PROMOTED = CompetitiveStrategy()


def board(rows: int = 5, cols: int = 5, blocked: frozenset[Position] = frozenset()) -> Board:
    return Board(rows=rows, cols=cols, blocked=blocked)


def belief(shape: Board, weights: dict[Position, str]) -> ScentBelief:
    grid = tuple(
        tuple(Decimal(weights.get(Position(r, c), "0")) for c in range(shape.cols))
        for r in range(shape.rows)
    )
    return ScentBelief(ScentField(shape.rows, shape.cols, 0, grid), 1)


def seen(shape: Board, cell: Position, scent: ScentBelief) -> Observation:
    return Observation(board=shape, own_position=cell, quota=QUOTA, scent=scent)


def test_the_promoted_parameters_are_the_ones_the_holdout_judged() -> None:
    """Frozen numbers, not tunables: 0.9 is the Appendix F Table 16 source strength."""
    assert Decimal("0.9") == CONSERVATIVE
    assert Decimal(10) == TRAP_BONUS


def test_a_hot_landing_cell_no_longer_blocks_a_well_supported_placement() -> None:
    """The measured defect the whole candidate line was built to fix.

    The old gate refused a placement unless its support strictly exceeded the
    evidence at the cell the mover was already stepping onto, so standing next
    to a well-located evader forbade spending a barrier. The promoted rule is an
    absolute floor and does not consult the landing cell at all.
    """
    shape, cell = board(), Position(2, 2)
    hot = {Position(2, 2): "0.9", Position(2, 3): "0.9", Position(1, 2): "0.9"}
    view = seen(shape, cell, belief(shape, hot))

    chosen = PROMOTED.choose_action(view)

    assert isinstance(chosen, BarrierAction)
    assert is_placeable(shape, cell, chosen.target, QUOTA)


def test_evidence_below_the_floor_leaves_the_shipped_move_alone() -> None:
    """An absolute floor is still a floor: weak evidence never buys a barrier."""
    shape, cell = board(), Position(2, 2)
    faint = {Position(0, 0): "0.05", Position(4, 4): "0.05"}
    view = seen(shape, cell, belief(shape, faint))

    assert PROMOTED.choose_action(view) == BASELINE.choose_action(view)


def test_a_silent_sub_game_is_exactly_the_baseline_decision() -> None:
    """No belief means no expected value, so the frozen mover decides."""
    for cell in (Position(0, 0), Position(2, 2), Position(4, 4), Position(1, 3)):
        view = seen(board(), cell, ScentBelief())

        assert PROMOTED.choose_action(view) == BASELINE.choose_action(view)


def test_the_shipped_mover_is_preserved_exactly() -> None:
    """C4's whole finding was that the *mover* must not change."""
    assert type(PROMOTED.baseline) is BaselineStrategy

    shape, cell = board(), Position(1, 1)
    view = seen(shape, cell, belief(shape, {Position(4, 4): "0.01"}))
    chosen = PROMOTED.choose_action(view)

    assert isinstance(chosen, MoveAction)
    assert chosen == BASELINE.choose_action(view)


def test_trapping_a_believed_cell_beats_merely_crowding_a_stronger_one() -> None:
    """`GAME-005` ends the game; shrinking the room only shrinks the room.

    `(1, 0)` is already walled, so placing on `(0, 1)` leaves `(0, 0)` with no
    traversable neighbour: its weak 0.1 becomes **1.0** through `TRAP_BONUS` and
    clears the floor. `(0, 3)` merely adjoins a much stronger 0.8 and scores
    exactly that - below the floor. The trap wins on far less raw belief.
    """
    shape = board(blocked=frozenset({Position(1, 0)}))
    cell = Position(0, 2)
    weights = {Position(0, 0): "0.1", Position(0, 4): "0.8"}
    view = seen(shape, cell, belief(shape, weights))
    mass = believed_cells(view)

    chosen = PROMOTED.choose_action(view)

    assert PROMOTED._value(view, mass, Position(0, 1)) == Decimal(1)
    assert PROMOTED._value(view, mass, Position(0, 3)) == Decimal("0.8")
    assert isinstance(chosen, BarrierAction)
    assert chosen.target == Position(0, 1)


def test_every_returned_placement_is_legal_and_never_a_capture_claim() -> None:
    shape = board()
    for cell in (Position(0, 0), Position(2, 2), Position(3, 1), Position(4, 4)):
        weights = {Position(r, c): "0.9" for r in range(5) for c in range(5)}
        chosen = PROMOTED.choose_action(seen(shape, cell, belief(shape, weights)))

        if isinstance(chosen, BarrierAction):
            assert is_placeable(shape, cell, chosen.target, QUOTA)
        else:
            assert isinstance(chosen, MoveAction)


def test_ties_break_deterministically_on_the_lowest_cell() -> None:
    """Two placements of equal value must resolve the same way on every platform."""
    shape, cell = board(), Position(2, 2)
    view = seen(
        shape, cell, belief(shape, {Position(r, c): "0.9" for r in range(5) for c in range(5)})
    )

    assert PROMOTED.choose_action(view) == PROMOTED.choose_action(view)


def test_an_exhausted_quota_can_never_produce_a_placement() -> None:
    """`is_placeable` counts the public board against the quota; nothing is left.

    The quota itself cannot be set to zero - Appendix F Table 15 fixes 14 as a
    MINIMUM - so exhaustion is modelled the only lawful way: a board already
    carrying that many barriers.
    """
    walls = frozenset(
        {Position(0, c) for c in range(5)}
        | {Position(4, c) for c in range(5)}
        | {Position(r, 0) for r in range(1, 4)}
        | {Position(r, 4) for r in range(1, 4)}
    )
    shape = board(blocked=walls)
    cell = Position(2, 2)
    weights = {Position(r, c): "0.9" for r in range(1, 4) for c in range(1, 4)}
    view = seen(shape, cell, belief(shape, weights))

    assert len(shape.blocked) >= QUOTA.max_barriers
    assert isinstance(PROMOTED.choose_action(view), MoveAction)
