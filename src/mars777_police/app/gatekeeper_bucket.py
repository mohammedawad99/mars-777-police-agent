"""The token bucket the source names, implemented as the source states it.

Appendix E rule 28 is a MUST and it names the algorithm: *"implement a
**token-bucket** based rate limiter for sending the reports to Gmail"*, with the
sanction *"preventing a 429 block that would paralyse the group's reporting"*.
Ch 9 §9.3.2 gives the rule itself, and it is transcribed here rather than
approximated:

    tokens <- min(C, tokens + r * dt),    allow <=> tokens >= 1

`C` is the capacity - how large a burst is permitted after a quiet period. `r`
is the refill rate - the sustained average that must stay under the provider's
quota. `dt` is the time since the last refill, so silence is rewarded with
future burst capacity.

**This is not the rolling window.** A rolling window answers *"how many calls
happened in the last minute"*; a bucket answers *"has enough time passed to have
earned a whole token"*. They are close in the long run and different in a burst,
and the source asked for the bucket by name - so describing the window as one
would have been a false claim with a passing test behind it.

**A rate token is not an LLM token and not an OAuth token.** Ch 9 says so
explicitly, in its own box, because all three appear in this project.
"""

from collections.abc import Callable
from dataclasses import dataclass, field

WHOLE = 1.0
"""One report costs one whole token: `allow <=> tokens >= 1`."""


@dataclass(slots=True)
class TokenBucket:
    """A refilling allowance for one provider operation."""

    capacity: float
    refill_per_second: float
    monotonic: Callable[[], float]
    tokens: float = field(default=-1.0)
    last: float = field(default=-1.0)

    def __post_init__(self) -> None:
        if self.capacity < WHOLE:
            raise ValueError("a token bucket that cannot hold one token admits nothing")
        if self.refill_per_second <= 0:
            raise ValueError("a token bucket that never refills admits nothing twice")
        if self.tokens < 0:
            self.tokens = self.capacity
        if self.last < 0:
            self.last = self.monotonic()

    def _refill(self) -> None:
        """`tokens <- min(C, tokens + r * dt)`, and never past the capacity.

        The clock is monotonic, so `dt` cannot be negative and the level cannot
        be inflated by a wall-clock correction.
        """
        now = self.monotonic()
        elapsed = max(0.0, now - self.last)
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_per_second)
        self.last = now

    @property
    def level(self) -> float:
        """The current level, refilled to now. Never above `C`, never below zero."""
        self._refill()
        return self.tokens

    def check(self) -> None:
        """A bucket refuses nothing outright; it only ever asks a caller to wait."""

    def wait_seconds(self) -> float:
        """Seconds until a whole token exists: `0.0` when one does right now."""
        self._refill()
        if self.tokens >= WHOLE:
            return 0.0
        return (WHOLE - self.tokens) / self.refill_per_second

    def stamp(self) -> None:
        """Spend one whole token for a call being made now.

        Spending is unconditional because admission already waited for the
        token; the floor at zero is what keeps a bucket that was raced from
        going negative and lending against the future.
        """
        self._refill()
        self.tokens = max(0.0, self.tokens - WHOLE)
