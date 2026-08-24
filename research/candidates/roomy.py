"""P7 - look ahead only while the evader still has somewhere to go.

**Built from a measured regression, not from a hunch.** P6 gained on five
families and lost 37 captures on `adversarial_corner`, the one family that
deliberately walks itself into tight regions. That is not noise and it is not a
coefficient: worst-case search is pessimistic by construction, and against an
evader busy trapping itself the pessimism is unwarranted. Declining a close
because a cornered evader *could* flee gives up captures it was never going to
take.

**So the ply is spent where it pays.** When the region reachable from the
strongest believed cell is large, the evader genuinely can step away and
anticipating that is worth a move; when it is small, the evader has already lost
the room the search was hedging against, and the shipped policy's directness
wins. One question, asked of the state.

**The question is behavioural, never an identity.** Reachable region from a
believed cell is a legal observable derived from the board and our own evidence.
Any opponent that walks into a tight region gets the same treatment, whoever it
is, and an opponent that stops doing so stops receiving it - which is the
property that makes this generalise rather than fit.

**The measure is local mobility, after a share of reachable region failed.**
The first version asked what fraction of our own reachable region the evader
could reach, and it reproduced P6 exactly: on an open board both walk the same
connected component, so the ratio is 1.0 almost everywhere and the gate never
fired. Sampled across corner, edge and centre states at three blocked densities
it read 1.0 in eleven of fifteen. Connectivity is not confinement. The count of
legal moves available at the believed cell does discriminate over the same
sample, and is the more direct statement of the thing being asked: whether the
evader has anywhere to go *right now*.
"""

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Final

from mars777_police.app.competitive_strategy import CompetitiveStrategy
from mars777_police.domain.actions import MoveAction, PhysicalAction
from mars777_police.domain.observation import Observation
from mars777_police.domain.reachability import reachable_from
from mars777_police.domain.rules import legal_moves

from .lookahead import LookaheadStrategy, believed_position

REVISION: Final[str] = "p7-roomy-2"

MOBILE: Final[int] = 4
"""Legal moves the evader needs before anticipating its reply is worth a move."""


def evader_room(observation: Observation) -> Decimal:
    """The believed region as a share of everywhere we can still walk.

    Kept because it is what the first revision gated on, and because a reader
    comparing revisions should be able to see the measure that failed rather
    than find it deleted. It is no longer consulted.
    """
    target = believed_position(observation)
    if target is None:
        return Decimal(0)
    ours = len(reachable_from(observation.board, observation.own_position)) or 1
    return Decimal(len(reachable_from(observation.board, target))) / Decimal(ours)


def evader_mobility(observation: Observation) -> int:
    """How many legal moves the evader has from the strongest believed cell.

    Zero when nothing is believed, which reads as cornered and defers to the
    shipped policy - the right answer, because a search with no target is a move
    spent on nothing.
    """
    target = believed_position(observation)
    if target is None:
        return 0
    return len(legal_moves(observation.board, target))


@dataclass(frozen=True, slots=True)
class RoomyLookaheadStrategy:
    """Anticipate an evader that can still run; close directly on one that cannot."""

    shipped: CompetitiveStrategy = field(default_factory=CompetitiveStrategy)
    searching: LookaheadStrategy = field(default_factory=LookaheadStrategy)
    mobile: int = MOBILE

    def searches(self, observation: Observation) -> bool:
        """Whether this state is one where anticipating a reply is worth a move."""
        return evader_mobility(observation) >= self.mobile

    def choose_action(self, observation: Observation) -> PhysicalAction:
        """Defer to the shipped policy for barriers and for cornered evaders."""
        shipped = self.shipped.choose_action(observation)
        if not isinstance(shipped, MoveAction) or not self.searches(observation):
            return shipped
        return self.searching.choose_action(observation)
