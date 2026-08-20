"""C2 and C3 - belief-valued barriers, at two frozen thresholds.

**The measured problem, which is not the one first assumed.** The shipped gate
admits a placement only when its support **strictly exceeds** the evidence at
the cell the mover was already going to. Measured over development scenarios,
that rule blocked the gate in **700 of 753** belief-carrying steps against
`adversarial_corner`, where the mean evidence at the chosen landing was
**0.825** - the police was standing next to a well-located thief and was
structurally forbidden from spending a barrier, because the same policy had just
walked onto the hottest cell. Against `evasive` the block was rare (50 of 816)
for the opposite reason: the belief is weak everywhere, mean **0.099**, so
almost nothing clears any bar.

So the gate's comparison is against the wrong quantity. A hot landing cell is
**evidence to act**, not a reason to abstain.

**The candidate rule.** Score a lawful placement by what it is expected to be
worth against the belief, and admit it on an absolute, source-anchored floor:

    value(target) = belief[target]                                  # BAR-003 route
                  + SUM over c of belief[c] * TRAP_BONUS  if placing traps c
                  + SUM over c of belief[c]               if target adjoins c
    place the best target when  value(target) >= threshold

`TRAP_BONUS = 10` because trapping is an immediate win under `GAME-005` while a
mobility reduction is only a nudge, and ten is an order of magnitude above any
single cell's belief, which Appendix F Table 16 caps at **0.9**.

**The two thresholds are frozen here, before any outcome was known**, and both
are anchored to that same FIXED source strength rather than fished for:

* `CONSERVATIVE = 0.9` - act when the expected evidence is worth a full emission
  at its source;
* `AGGRESSIVE = 0.3` - one third of that, to test whether the baseline's ~3.4
  placements from a quota of 14 is a missed opportunity or simply the number of
  placements that were ever worth making.

Neither is "always place": both require a positive expected value, and legality
is still decided entirely by `is_placeable`.

**C4 is the ablation this rule made askable.** C1 measured the mover alone and
collapsed; C2 measures mover **and** rule together. Neither answers which half
carries the gain, so C4 runs this same rule behind the **shipped** mover. Its
formula is the one above, unchanged, at the conservative floor - frozen before
it was run.
"""

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Final

from mars777_police.app.baseline_strategy import BaselineStrategy
from mars777_police.domain.actions import BarrierAction, PhysicalAction
from mars777_police.domain.barrier_effect import newly_trapped
from mars777_police.domain.barriers import is_placeable
from mars777_police.domain.board import Position
from mars777_police.domain.observation import Observation

from .pursuit import PursuitMover, belief_cells

REVISION = "r1"
CONSERVATIVE: Final[Decimal] = Decimal("0.9")
AGGRESSIVE: Final[Decimal] = Decimal("0.3")
TRAP_BONUS: Final[Decimal] = Decimal(10)
ZERO = Decimal(0)


@dataclass(frozen=True, slots=True)
class DenialStrategy:
    """C1's mover, with a belief-valued barrier rule in front of it."""

    threshold: Decimal
    mover: BaselineStrategy = field(default_factory=PursuitMover)
    """Which mover runs when no placement clears the floor. Widened so C4 can
    inject the **shipped** mover and isolate which half of C2 does the work."""

    def choose_action(self, observation: Observation) -> PhysicalAction:
        """Place when the expected value clears the floor, otherwise pursue."""
        mass = belief_cells(observation)
        best = self._best_target(observation, mass)
        if best is None:
            return self.mover.choose_action(observation)
        return BarrierAction(best)

    def _targets(self, observation: Observation) -> tuple[Position, ...]:
        """The lawful placements, decided entirely by `is_placeable`."""
        board, actor = observation.board, observation.own_position
        return tuple(
            cell
            for cell in board.orthogonal_neighbours(actor)
            if is_placeable(board, actor, cell, observation.quota)
        )

    def _best_target(
        self, observation: Observation, mass: tuple[tuple[Position, Decimal], ...]
    ) -> Position | None:
        """The most valuable placement that clears the floor, or nothing."""
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
        """Expected worth of placing at *target*, against the lawful belief only."""
        trapped = set(
            newly_trapped(observation.board, observation.own_position, target, observation.quota)
        )
        neighbours = set(observation.board.orthogonal_neighbours(target))
        total = ZERO
        for cell, weight in mass:
            if cell == target:
                total += weight
            if cell in trapped:
                total += weight * TRAP_BONUS
            elif cell in neighbours:
                total += weight
        return total
