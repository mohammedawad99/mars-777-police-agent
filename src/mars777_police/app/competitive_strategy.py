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

**The barrier must earn the turn.** `BaselineStrategy` stays the frozen
reference and decides the move; a placement displaces that move only when the
evidence supporting it is *strictly* stronger than the evidence at the cell the
baseline would have moved to. Empty, uniform or merely equal evidence therefore
reproduces the baseline exactly - which is what makes this safe to ship and what
the regression corpus pins.

**Two families, one gate, no weighted score.** Moves and placements are never
mixed into a single tuple: the admission gate decides *whether* a placement
competes, and a separate lexicographic order decides *which*. Every comparison
is exact - `Decimal` from the scent authority and integers - so no coefficient
is invented and no platform can disagree.

Nothing here claims the thief occupies anything, and nothing here decides
legality: candidates come from `is_placeable` and `legal_moves`, and
`LocalTurnService` still revalidates whatever is returned.
"""

from dataclasses import dataclass, field
from decimal import Decimal

from ..domain.actions import BarrierAction, PhysicalAction
from ..domain.barrier_effect import newly_trapped
from ..domain.barriers import is_placeable
from ..domain.board import Position
from ..domain.observation import Observation
from ..domain.rules import destination_of
from .baseline_strategy import BaselineStrategy

NO_SUPPORT = Decimal("0")
"""The evidence a cell nobody has been near carries."""


@dataclass(frozen=True, slots=True)
class Support:
    """What one candidate placement has going for it, in ranking order."""

    total: Decimal
    trap: Decimal
    cornered: int
    direct: Decimal
    target: Position

    def order(self) -> tuple[Decimal, Decimal, int, Decimal, int, int]:
        """The lexicographic key, negated where a larger value should win."""
        return (
            -self.total,
            -self.trap,
            -self.cornered,
            -self.direct,
            self.target.row,
            self.target.col,
        )


@dataclass(frozen=True, slots=True)
class CompetitiveStrategy:
    """A stateless, deterministic, zero-token police policy with barrier pressure."""

    baseline: BaselineStrategy = field(default_factory=BaselineStrategy)

    def choose_action(self, observation: Observation) -> PhysicalAction:
        """The baseline move, unless a placement is better supported than it is."""
        move = self.baseline.choose_action(observation)
        landing = destination_of(observation.own_position, move.move)  # type: ignore[union-attr]
        admitted = [
            support
            for target in self._targets(observation)
            if (support := self._support(observation, target)).total > NO_SUPPORT
            and support.total > observation.scent.intensity_at(landing)
        ]
        if not admitted:
            return move
        return BarrierAction(min(admitted, key=Support.order).target)

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

    def _support(self, observation: Observation, target: Position) -> Support:
        """How strongly the lawful evidence backs placing a barrier on *target*.

        Two independent routes, and the stronger one speaks: the evidence on the
        target itself (BAR-003 would capture a thief standing there) and the
        strongest evidence on any cell the placement would newly corner
        (GAME-005 would capture a thief left there). Neither asserts occupancy.
        """
        direct = observation.scent.intensity_at(target)
        cornered = newly_trapped(
            observation.board, observation.own_position, target, observation.quota
        )
        trap = max((observation.scent.intensity_at(cell) for cell in cornered), default=NO_SUPPORT)
        return Support(max(direct, trap), trap, len(cornered), direct, target)
