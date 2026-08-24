"""P5 - state-based arbitration between pursuit and containment.

**Why arbitration rather than another weighting.** Earlier cycles measured two
kinds of Police behaviour and found each strong where the other is weak. A
belief-directed pursuer closes distance well once it has evidence, and wanders
when it has none. A containment rule that spends barriers to sever region is
worth most when the evader still has room and worth little when capture is one
step away and a forgone move throws it away. Averaging them produces a policy
that is second-best everywhere; choosing between them per state does not.

**The selector reads state, never identity.** Three legal observable features
decide the mode, all of which any opponent exhibiting the same behaviour would
produce:

* *immediate threat* - whether a believed cell is adjacent, so a capture is
  available now and containment would squander it;
* *evader room* - the size of the region reachable from the strongest believed
  cell, as a fraction of the open board, which says whether there is anything
  left to contain;
* *evidence* - whether any belief exists at all, because with none there is no
  region to reason about and no target to pursue.

Nothing here consults a group id, a repository, a commit, a game number or a
remembered trajectory. An unknown opponent producing the same observable state
gets the same decision, which is the only property that makes this general.

**Lexicographic, not scored.** The modes are chosen by an ordered set of
questions rather than by summing weighted features. A weighted sum invites
coefficient fitting, and this cycle has no evidence that would justify any
particular coefficient; an ordered rule states the reasoning instead and can be
argued with directly.

**Legality is untouched.** Both delegates come from the existing policies, both
already return actions drawn from `is_placeable` and the legal move set, and
`LocalTurnService` revalidates whatever is returned. This module decides which
policy answers, never what is legal.
"""

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Final

from mars777_police.app.baseline_strategy import BaselineStrategy
from mars777_police.app.competitive_strategy import CompetitiveStrategy, believed_cells
from mars777_police.domain.actions import PhysicalAction
from mars777_police.domain.board import Position
from mars777_police.domain.observation import Observation
from mars777_police.domain.reachability import reachable_from

from . import mobility

REVISION: Final[str] = "p5-arbiter-1"

ROOMY: Final[Decimal] = Decimal("0.45")
"""The share of the open board the evader must still reach for containment to
have something to work on. Below it, severing region buys little that pursuit
would not already take."""


def _adjacent(one: Position, other: Position) -> bool:
    """Orthogonally adjacent - the geometry a capture actually needs."""
    return abs(one.row - other.row) + abs(one.col - other.col) == 1


def strongest(observation: Observation) -> Position | None:
    """The most-believed cell, or `None` when nothing is believed at all."""
    believed = believed_cells(observation)
    if not believed:
        return None
    return max(believed, key=lambda pair: (pair[1], -pair[0].row, -pair[0].col))[0]


def threat_is_immediate(observation: Observation) -> bool:
    """Whether a believed cell sits one step away, so capture is available now."""
    return any(_adjacent(observation.own_position, cell) for cell, _ in believed_cells(observation))


def evader_room(observation: Observation) -> Decimal:
    """The believed region's size as a share of everywhere we can still walk.

    Measured from the strongest believed cell because that is the only place
    this policy has lawful evidence the evader might be. Zero when nothing is
    believed: an unknown evader has no measurable room, and pretending otherwise
    would let silence look like containment succeeding.
    """
    target = strongest(observation)
    if target is None:
        return Decimal(0)
    ours = len(reachable_from(observation.board, observation.own_position)) or 1
    theirs = len(reachable_from(observation.board, target))
    return Decimal(theirs) / Decimal(ours)


@dataclass(frozen=True, slots=True)
class ArbiterStrategy:
    """Pursuit when capture is near or evidence is thin; containment when neither."""

    pursue: CompetitiveStrategy = field(default_factory=CompetitiveStrategy)
    contain: mobility.MobilityDenialStrategy = field(
        default_factory=mobility.MobilityDenialStrategy
    )
    roomy: Decimal = ROOMY

    def mode(self, observation: Observation) -> str:
        """Which delegate answers, and the ordered reasons that decide it."""
        if not believed_cells(observation):
            return "pursue"
        if threat_is_immediate(observation):
            return "pursue"
        if evader_room(observation) < self.roomy:
            return "pursue"
        return "contain"

    def choose_action(self, observation: Observation) -> PhysicalAction:
        """Delegate to the mode this state selects. Legality stays downstream."""
        if self.mode(observation) == "contain":
            return self.contain.choose_action(observation)
        return self.pursue.choose_action(observation)


def baseline() -> BaselineStrategy:
    """The unmodified shipped mover, for a screen that needs it by name."""
    return BaselineStrategy()
