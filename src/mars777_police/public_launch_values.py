"""What an operator may safely be shown while a public route is live.

Every member is a fact somebody outside this process could already learn, or a
fact about our own posture that costs nothing to state. What is deliberately
absent is everything else: no authentication key, no tunnel credential, no
private backend endpoint, no strategy internals, no game state.

`counted_eligible` is derived from the run class rather than stored, for the
same reason it is everywhere else - a public route is still a development
friendly, and no banner should be able to say otherwise.
"""

from dataclasses import dataclass

from .app.kit_schedule import CONVENTION, SUB_GAMES
from .app.run_class import RunClass


@dataclass(frozen=True, slots=True)
class PublicLaunchStatus:
    """The operator banner, as a value rather than as print statements."""

    group_id: str
    public_endpoint: str | None
    run_class: RunClass
    evidence_root: str
    backends_configured: int

    @property
    def counted_eligible(self) -> bool:
        """A public route promotes nothing. Always false for a friendly."""
        return self.run_class is not RunClass.KIT_FRIENDLY_ONLY

    def operator_lines(self) -> tuple[str, ...]:
        """The exact lines printed at startup, and nothing beyond them."""
        return (
            f"group_id            {self.group_id}",
            f"public endpoint     {self.public_endpoint or 'WAITING - not yet discovered'}",
            f"run class           {self.run_class.value} (counted play: NOT READY)",
            f"series convention   {CONVENTION.value}, {SUB_GAMES} sub-games",
            f"role backends       {self.backends_configured} configured (private, not advertised)",
            f"evidence written to {self.evidence_root}",
        )
