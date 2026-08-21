"""The police policy that may spend a barrier when the evidence supports one.

Ch 6 §6.3.1 leaves the movement policy to the group and §6.1/§6.6 require only
that the spatial decision stay algorithmic, so this is **PROJECT-DERIVED**
optional competitive strategy - not a source mandate, not Bayes, not learning,
and not a claim of optimality.

**Why a barrier at all.** BAR-004 lets the police forgo its move to place one,
and two lawful routes make that meaningful: BAR-003 captures a thief standing
on the target, and GAME-005 captures one left with no traversable neighbour.
Neither needs a `CaptureClaim`, which is the whole reason this is the safe lever
to pull - a wrong claim is a `FALSE_CAPTURE_CLAIM` technical loss for the
claimant, while a barrier that simply misses is an ordinary legal action that
produces no finding at all. Belief may therefore fund a barrier; it may never
fund a declaration.

**The gate is an absolute floor, and this is the measured correction.** Until
Stage 9B-2 a placement had to be supported *strictly more strongly* than the
cell the mover was already stepping onto. Instrumenting the belief showed that
rule blocked **334 of 375** belief-carrying decisions against a well-located
evader (mean evidence at that landing cell **0.822**), while blocking at most
8.2% against every other opponent family: the policy walked onto the hottest
square and then forbade itself the barrier. A hot landing cell is evidence to
act, not a reason to abstain, so the landing cell is no longer consulted and the
floor is absolute.

**The score is an expectation over the lawful belief**, not the single strongest
route:

    value(t) = belief[t]                          # BAR-003 would capture there
             + SUM belief[c] * TRAP_BONUS         # c newly cornered: GAME-005
             + SUM belief[c]                      # c adjacent to t: less room

`TRAP_BONUS = 10` because cornering ends the game while a mobility reduction
only shrinks it, and ten is an order of magnitude above any single cell, which
Appendix F Table 16 caps at **0.9**. The floor is that same FIXED source
strength: act when the expected evidence is worth a full emission at its source.

**`BaselineStrategy` still decides every move.** That is a measured result, not
an omission: a belief-directed mover was evaluated as its own candidate and
**collapsed**, losing every game the shipped policy had won, and the ablation
that kept this mover beat the one that replaced it. Empty belief therefore
reproduces the baseline exactly.

**Two families, one gate, no weighted score.** Moves and placements are never
mixed into a single tuple: the gate decides *whether* a placement competes, and
a separate lexicographic order decides *which*. Every comparison is exact -
`Decimal` from the scent authority and integers - so no coefficient is invented
and no platform can disagree.

Nothing here claims the thief occupies anything, and nothing here decides
legality: candidates come from `is_placeable` and `legal_moves`, and
`LocalTurnService` still revalidates whatever is returned.
"""

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Final

from ..domain.actions import BarrierAction, PhysicalAction
from ..domain.barrier_effect import newly_trapped
from ..domain.barriers import is_placeable
from ..domain.board import Position
from ..domain.observation import Observation
from .baseline_strategy import BaselineStrategy

NO_SUPPORT = Decimal("0")
"""The evidence a cell nobody has been near carries."""

CONSERVATIVE: Final[Decimal] = Decimal("0.9")
"""The floor: one full emission at its source (Appendix F Table 16, FIXED)."""

TRAP_BONUS: Final[Decimal] = Decimal(10)
"""Cornering ends the game; crowding only shrinks it."""


def believed_cells(observation: Observation) -> tuple[tuple[Position, Decimal], ...]:
    """Every cell carrying lawful evidence, with its intensity. Empty when silent."""
    if not observation.scent.has_evidence:
        return ()
    board = observation.board
    found: list[tuple[Position, Decimal]] = []
    for row in range(board.rows):
        for col in range(board.cols):
            cell = Position(row + board.start_index, col + board.start_index)
            intensity = observation.scent.intensity_at(cell)
            if intensity > NO_SUPPORT:
                found.append((cell, intensity))
    return tuple(found)


@dataclass(frozen=True, slots=True)
class CompetitiveStrategy:
    """A stateless, deterministic, zero-token police policy with barrier pressure."""

    baseline: BaselineStrategy = field(default_factory=BaselineStrategy)

    def choose_action(self, observation: Observation) -> PhysicalAction:
        """Place when the expected evidence clears the floor, otherwise move."""
        mass = believed_cells(observation)
        best = self._best_target(observation, mass)
        if best is None:
            return self.baseline.choose_action(observation)
        return BarrierAction(best)

    def _targets(self, observation: Observation) -> tuple[Position, ...]:
        """The lawful placements this policy is willing to consider.

        The actor's own cell is excluded even though BAR-004 permits it: walling
        the square we stand on is not the pressure this policy applies, and that
        is a strategy choice rather than a new legality rule - `is_placeable`
        still decides everything about whether a target is legal at all.
        """
        board, actor = observation.board, observation.own_position
        return tuple(
            neighbour
            for neighbour in board.orthogonal_neighbours(actor)
            if is_placeable(board, actor, neighbour, observation.quota)
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
        admitted = [one for one in scored if one[0] >= CONSERVATIVE]
        if not admitted:
            return None
        return min(admitted, key=lambda one: (-one[0], one[1].row, one[1].col))[1]

    def _value(
        self,
        observation: Observation,
        mass: tuple[tuple[Position, Decimal], ...],
        target: Position,
    ) -> Decimal:
        """Expected worth of placing on *target*, against the lawful belief only."""
        trapped = set(
            newly_trapped(observation.board, observation.own_position, target, observation.quota)
        )
        neighbours = set(observation.board.orthogonal_neighbours(target))
        total = NO_SUPPORT
        for cell, weight in mass:
            if cell == target:
                total += weight
            if cell in trapped:
                total += weight * TRAP_BONUS
            elif cell in neighbours:
                total += weight
        return total
