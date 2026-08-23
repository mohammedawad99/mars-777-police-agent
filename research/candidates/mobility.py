"""V3 - the §15 hypothesis 2 that was never implemented: deny region, not cells.

**The idea, and the reason it is worth a candidate at all.** The shipped rule
scores a placement by the belief it directly touches: the target cell, the cells
it would newly trap, and the cells it adjoins. That is a *local* measure. An
evader does not survive by standing on a good cell; it survives by having
somewhere to go. A barrier that removes very little belief but severs a corridor
can be worth far more than one that sits next to a hot cell in open board.

**The candidate rule.** Keep the shipped value exactly as it is - the same three
terms, the same `TRAP_BONUS`, the same absolute floor - and add one term for the
region the placement actually removes from the evader:

    denial(target) = |reachable(before)| - |reachable(after)|

measured from the strongest believed cell, because that is the only place this
policy has any evidence the evader might be. The term enters the *score*, never
the floor: a placement still has to clear the same admission threshold, so this
cannot become "place more" by the back door - which §16 already measured and
found is not by itself a gain.

**Weighting, and why it is one and not tuned.** Each severed cell counts as one
unit of the belief at the cell it is denied to, so the term is commensurate with
the existing ones rather than scaled by a coefficient somebody chose. There is no
free parameter here to fit.

**Reachability is the barrier-aware one.** `domain.reachability` walks the board
as a graph through the board's own traversability rule, so a corridor that only
*looks* open is not counted as open. This module decides no legality: candidates
still come from `is_placeable`, and `LocalTurnService` revalidates whatever is
returned.
"""

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Final

from mars777_police.app.baseline_strategy import BaselineStrategy
from mars777_police.domain.actions import BarrierAction, PhysicalAction
from mars777_police.domain.barrier_effect import newly_trapped
from mars777_police.domain.barriers import is_placeable, place_barrier
from mars777_police.domain.board import Position
from mars777_police.domain.observation import Observation
from mars777_police.domain.reachability import reachable_from

from .pursuit import belief_cells

REVISION = "r1"
CONSERVATIVE: Final[Decimal] = Decimal("0.9")
TRAP_BONUS: Final[Decimal] = Decimal(10)
ZERO = Decimal(0)


@dataclass(frozen=True, slots=True)
class MobilityDenialStrategy:
    """The shipped rule, plus the region a placement removes from the evader."""

    threshold: Decimal = CONSERVATIVE
    mover: BaselineStrategy = field(default_factory=BaselineStrategy)

    def choose_action(self, observation: Observation) -> PhysicalAction:
        """Place when the expected worth clears the floor, otherwise move."""
        mass = belief_cells(observation)
        target = self._best(observation, mass)
        if target is None:
            return self.mover.choose_action(observation)
        return BarrierAction(target)

    def _targets(self, observation: Observation) -> tuple[Position, ...]:
        board, actor = observation.board, observation.own_position
        return tuple(
            neighbour
            for neighbour in board.orthogonal_neighbours(actor)
            if is_placeable(board, actor, neighbour, observation.quota)
        )

    def _best(
        self, observation: Observation, mass: tuple[tuple[Position, Decimal], ...]
    ) -> Position | None:
        if not mass:
            return None
        scored = [
            (self._value(observation, mass, target), target)
            for target in self._targets(observation)
        ]
        admitted = [one for one in scored if one[0] >= self.threshold]
        if not admitted:
            return None
        return min(admitted, key=lambda one: (-one[0], one[1].row, one[1].col))[1]

    def _value(
        self,
        observation: Observation,
        mass: tuple[tuple[Position, Decimal], ...],
        target: Position,
    ) -> Decimal:
        """The shipped three terms, plus the region this placement denies."""
        board = observation.board
        trapped = set(newly_trapped(board, observation.own_position, target, observation.quota))
        neighbours = set(board.orthogonal_neighbours(target))
        total = ZERO
        for cell, weight in mass:
            if cell == target:
                total += weight
            if cell in trapped:
                total += weight * TRAP_BONUS
            elif cell in neighbours:
                total += weight
        return total + self._denied(observation, mass, target)

    @staticmethod
    def _denied(
        observation: Observation,
        mass: tuple[tuple[Position, Decimal], ...],
        target: Position,
    ) -> Decimal:
        """Belief-weighted cells the placement removes from the evader's region.

        Measured from the strongest believed cell, deterministically: ties break
        on the lowest row then column, so two cells of equal evidence cannot let
        iteration order decide a placement.
        """
        board = observation.board
        cell, weight = max(mass, key=lambda one: (one[1], -one[0].row, -one[0].col))
        if cell == target:
            return ZERO
        after = place_barrier(board, observation.own_position, target, observation.quota)
        before = len(reachable_from(board, cell))
        return weight * Decimal(max(before - len(reachable_from(after, cell)), 0))
