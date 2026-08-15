"""The police baseline: stand where the most of the board is easiest to reach.

Ch 6 §6.3.1 offers three equal tracks for movement policy - Bayesian belief with
Manhattan distance, your own heuristic, or optionally RL - and says the choice
belongs to the group. Ch 10 §10.3.3 places a **blind** module at this stage,
*"blind in the sense that there is not yet scent, natural language or
deception"*. This is that module, and the heuristic below is **PROJECT-DERIVED**:
the source mandates no algorithm, only that the spatial decision stay
algorithmic (§6.1, §6.6).

**What a pursuer can honestly optimise while knowing nothing.** With no belief
there is no target, so there is no distance to minimise *to* anything. What
remains is being reachable: prefer the cell whose total barrier-aware distance
to everywhere still walkable is smallest. It is the same comparison the belief
stage will make - `PRD03-FR-013` minimises distance to the believed cell - with
the target set not yet narrowed, so belief refines this rule instead of
replacing it.

**Two consequences stated rather than hidden.** Once it already occupies the
most reachable cell it stays there, because nothing tells it where to go; that
is the anti-passivity gap `PRD03-FR-016` closes once a target exists. And the
comparison is between destinations of one actor's legal moves, which share a
connected region whenever that actor's own cell is traversable - the condition
under which their totals are commensurable.

**No barriers, deliberately.** Every non-arbitrary placement rule needs a
benefit measure, and `PRD03-FR-017`'s is belief-supported; the alternatives are
spending an irreversible quota on a schedule or reading the thief's cell, which
is forbidden. So the baseline places none. The seam is unaffected: the return
type is the full `PhysicalAction` union and `domain.barriers` is untouched and
ready.
"""

from dataclasses import dataclass

from ..domain.actions import MoveAction, PhysicalAction
from ..domain.observation import Observation
from ..domain.reachability import reachable_from
from ..domain.rules import Move, destination_of, legal_moves
from .protocol_errors import LocalDefectError


@dataclass(frozen=True, slots=True)
class BaselineStrategy:
    """A stateless, deterministic, zero-token police policy."""

    def choose_action(self, observation: Observation) -> PhysicalAction:
        """Return the legal move leaving the most of the board within reach.

        Candidates come from `legal_moves` and from nowhere else, so this policy
        cannot propose an action the validator would refuse for a reason it
        invented. Ties fall to `MOVE_ORDER`, which `legal_moves` already
        preserves - `min` keeps the first of equal scores, so the tie-break is
        the domain's published order rather than a second one declared here.
        """
        candidates = legal_moves(observation.board, observation.own_position)
        if not candidates:
            raise LocalDefectError(
                f"no legal action from {observation.own_position}: an actor with"
                " none is a terminal the caller settles before asking a strategy",
            )
        return MoveAction(min(candidates, key=lambda move: self._spread(observation, move)))

    def _spread(self, observation: Observation, move: Move) -> int:
        """Total walking distance from where *move* lands to all it can reach.

        Lower is more central. Integer throughout, so the comparison is exact
        and identical on every platform (`PRD03-FR-030`).
        """
        landing = destination_of(observation.own_position, move)
        return sum(reachable_from(observation.board, landing).values())
