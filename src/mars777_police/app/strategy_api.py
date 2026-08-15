"""The one seam a decision policy plugs into.

Ch 6 §6.2 is the requirement this module exists for: *"a clear development
requirement: the students must implement a **separate strategy module**,
connecting to the PeerRuntime layer at an exact point - immediately after
decoding the incoming hint, and before packing the outgoing Commit"*, because
*"this separation is not an architectural caprice; it is the border between a
generic communication component and a **thinking agent**"*.

`API_BOUNDARIES.md` already registers `StrategyPort` - caller *app turn
service*, owner *strategy plug-in*, `Observation` in, a proposed action out. This
is that row made callable, so the register still holds **21** ports and no new
identity is created. It is also the one row whose Python form is justified under
that document's own rule: a port is worth a `Protocol` when implementations are
genuinely interchangeable, which is exactly what a baseline that must later be
replaced by a competitive policy means.

**One operation, and nothing around it.** No `async` - deciding is pure
computation and `async` is an I/O property (**O1**). No deadline, no token
budget, no logging, no commitment and no language: each has an owner already,
and a seam that carried them would make swapping a policy a change to all of
them. What comes back is a `PhysicalAction`, the domain's own union - never a
`Reveal`, never a digest, never a claim about the outcome.
"""

from typing import Protocol

from ..domain.actions import PhysicalAction
from ..domain.observation import Observation


class StrategyPort(Protocol):
    """Selects this agent's next physical action from role-legal facts alone."""

    def choose_action(self, observation: Observation) -> PhysicalAction:
        """Return the action to attempt, given everything this side may see.

        A *proposal*: the returned action carries no authority of its own and is
        revalidated by `LocalTurnService.apply` before any effect exists, so a
        policy that returns an illegal action is refused rather than obeyed.
        """
        ...
