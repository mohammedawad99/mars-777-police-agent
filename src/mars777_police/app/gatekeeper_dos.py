"""The DOS detector: what stops our own bug from getting the account suspended.

Ch 9 §9.3.1 names it as the third cumulative mechanism, and Appendix E rule 29
makes it a MUST: *"identifies anomalous sending patterns that indicate a bug or
an infinite loop in the agent's code. Once such a pattern is identified, the
Gatekeeper **locks access to the API completely** and prevents suspension of the
account by the service provider - a principle known in systems development as
backpressure and circuit breaking."*

**The threat modelled is our own code, not a hostile peer.** Ch 9 asks the
question directly - *"what happens when an infinite loop starts firing thousands
of messages a minute?"* - so the detector watches our own call rate over a short
window and, once it is exceeded, stops answering at all.

**The lock is deliberately not self-healing.** A circuit breaker that reopened
on a timer would let an unfixed loop resume; this one stays shut for the life of
the process, and clearing it is an operator act after the defect is understood.
"""

from collections.abc import Callable
from dataclasses import dataclass, field


class ProviderLockedError(Exception):
    """The gate is shut: an anomalous send pattern was detected."""


@dataclass(slots=True)
class DosDetector:
    """Watches one operation's own call rate and latches shut when it is absurd."""

    burst_limit: int
    window_seconds: float
    monotonic: Callable[[], float]
    locked: bool = field(default=False)
    _stamps: list[float] = field(default_factory=list)

    def __post_init__(self) -> None:
        if type(self.burst_limit) is not int or self.burst_limit <= 0:
            raise ValueError("a DOS burst limit must permit at least one call")
        if self.window_seconds <= 0:
            raise ValueError("a DOS window must be a positive number of seconds")

    def check(self) -> None:
        """Refuse everything once the detector has latched."""
        if self.locked:
            raise ProviderLockedError(
                "the gate is locked: an anomalous sending pattern was detected,"
                " and it stays locked until the defect behind it is understood"
            )

    def wait_seconds(self) -> float:
        """A lock is not a delay: this mechanism never asks a caller to wait."""
        return 0.0

    def stamp(self) -> None:
        """Record a call, and latch shut if this operation is now firing absurdly."""
        now = self.monotonic()
        self._stamps = [one for one in self._stamps if now - one < self.window_seconds]
        self._stamps.append(now)
        if len(self._stamps) > self.burst_limit:
            self.locked = True
