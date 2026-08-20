"""What the harness will accept as a policy: exactly the production seam.

`app.strategy_api.StrategyPort` is the contract the counted agent decides
through - one `Observation` in, one `PhysicalAction` out - and the research
harness accepts nothing wider. Re-declared here rather than imported so the
research package states its own contract, and structurally identical so a
production strategy satisfies it without adaptation.

**This is the privacy seam.** A policy receives an `Observation` and nothing
else: no board writes, no opponent handle, no clock, no random stream, no run
state. Whatever a benchmark opponent knows, it knows because the observation
carried it.
"""

from typing import Protocol

from mars777_police.domain.actions import PhysicalAction
from mars777_police.domain.observation import Observation


class Policy(Protocol):
    """One decision, from one lawful observation, and nothing else."""

    def choose_action(self, observation: Observation) -> PhysicalAction:
        """Return the action this policy chooses. Legality is revalidated after."""
        ...
