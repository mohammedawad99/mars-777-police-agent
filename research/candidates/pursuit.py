"""C1 - belief-directed pursuit: move toward the mass, not toward the middle.

**The measured problem.** The shipped mover ranks a move by `spread` - the total
barrier-aware distance from its landing cell to everywhere still reachable -
which is a **target-free** objective: nothing in it refers to where the thief
might be. The lawful belief enters only as a *tie-break on one cell*, second in
the rank tuple, so it can separate two moves only when their `spread` is exactly
equal. On an open board that almost never happens, and the belief is discarded.

**The candidate.** Rank first by the belief-weighted expected distance to the
mass, and keep `spread` as the secondary term so a silent sub-game still prefers
the accessible cell:

    pursuit_cost(landing) = SUM over cells c of  belief[c] * manhattan(landing, c)
    rank(move) = ( pursuit_cost, spread, MOVE_ORDER )

**Safety by construction.** With no evidence the belief is zero everywhere, every
`pursuit_cost` is zero, and the ranking falls through to exactly the baseline's -
so a sub-game that has heard nothing plays identically to production. That is
what makes this candidate a strict extension rather than a replacement.

Manhattan rather than barrier-aware distance on purpose: it is the metric Ch 6
§6.3.1 names beside the belief track, it is exact in integers, and it costs
`O(cells)` per candidate move instead of a BFS per candidate move.

**It replaces the mover and nothing else.** `PursuitMover` is a drop-in for
`BaselineStrategy`, so C1 is the shipped `CompetitiveStrategy` with this mover
injected and its barrier gate untouched. That is what makes the measurement
attributable: one change, not two.
"""

from dataclasses import dataclass
from decimal import Decimal

from mars777_police.app.baseline_strategy import BaselineStrategy
from mars777_police.domain.actions import MoveAction, PhysicalAction
from mars777_police.domain.board import Position
from mars777_police.domain.observation import Observation
from mars777_police.domain.reachability import reachable_from
from mars777_police.domain.rules import Move, destination_of, legal_moves

NAME = "C1-pursuit"
REVISION = "r1"

ZERO = Decimal(0)


def belief_cells(observation: Observation) -> tuple[tuple[Position, Decimal], ...]:
    """Every cell carrying lawful evidence, with its intensity. Empty when silent."""
    if not observation.scent.has_evidence:
        return ()
    board = observation.board
    found: list[tuple[Position, Decimal]] = []
    for row in range(board.rows):
        for col in range(board.cols):
            cell = Position(row + board.start_index, col + board.start_index)
            intensity = observation.scent.intensity_at(cell)
            if intensity > ZERO:
                found.append((cell, intensity))
    return tuple(found)


def manhattan(one: Position, other: Position) -> int:
    """The metric Ch 6 §6.3.1 names beside the belief track. Exact integers."""
    return abs(one.row - other.row) + abs(one.col - other.col)


def pursuit_cost(landing: Position, mass: tuple[tuple[Position, Decimal], ...]) -> Decimal:
    """Belief-weighted expected distance from *landing* to the evidence.

    Zero for an empty belief, which is what makes a silent sub-game fall through
    to the baseline ordering unchanged.
    """
    return sum((weight * manhattan(landing, cell) for cell, weight in mass), ZERO)


@dataclass(frozen=True, slots=True)
class PursuitMover(BaselineStrategy):
    """C1's mover: a drop-in replacement for the shipped accessibility mover.

    A subclass rather than a look-alike so the shipped barrier gate accepts it
    without a cast: the gate asks its `baseline` for a move, and this is one.
    """

    def choose_action(self, observation: Observation) -> PhysicalAction:
        """The legal move minimising expected distance to the believed mass."""
        candidates = legal_moves(observation.board, observation.own_position)
        if not candidates:
            raise ValueError("a trapped actor is a terminal, not a decision")
        mass = belief_cells(observation)

        def rank(move: Move) -> tuple[Decimal, int]:
            return self._pursuit_rank(observation, mass, move)

        return MoveAction(min(candidates, key=rank))

    def _pursuit_rank(
        self,
        observation: Observation,
        mass: tuple[tuple[Position, Decimal], ...],
        move: Move,
    ) -> tuple[Decimal, int]:
        """Pursuit first, accessibility second, `MOVE_ORDER` third via `min`.

        The accessibility term is recomputed here rather than reached for inside
        the shipped policy: research may read production, never poke at its
        privates, and the definition is one line of the same public authority.
        """
        landing = destination_of(observation.own_position, move)
        spread = sum(reachable_from(observation.board, landing).values())
        return (pursuit_cost(landing, mass), spread)
