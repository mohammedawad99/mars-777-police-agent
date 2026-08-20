"""Which mechanisms decide whether one provider call may go out, and in what order.

Ch 9 §9.3.1 describes the Gatekeeper as **one** pattern made of *three
cumulative protection mechanisms* - a Quota Manager, a Token Bucket rate limiter
and a DOS Detector - and its own figure shows an outgoing report passing through
all three before it reaches the Gmail API, with a distinct exit at each:
`Rejected (quota full)`, `Blocked (no token)`, `LOCKED (anomaly)`.

So admission is a **chain**, not a class per gate, and this module is the seam:
one narrow protocol, one chain that owns the order, and one function that builds
the chain a configured policy asks for. The Gatekeeper itself gained nothing it
has to know about Gmail.

**The default is unchanged.** An operation that does not ask for the trio keeps
the rolling minute/hour windows that Stage 9A-1C shipped, byte for byte. The
token bucket exists because Appendix E rule 28 names it for **Gmail**, not
because rolling windows were wrong for a tunnel poll.
"""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol

from ..shared.rate_limits import RateLimitPolicy
from .gatekeeper_bucket import TokenBucket
from .gatekeeper_dos import DosDetector
from .gatekeeper_quota import DailyQuota
from .gatekeeper_windows import RollingWindows

ROLLING_WINDOW = "rolling_window"
TOKEN_BUCKET = "token_bucket"


class AdmissionPolicy(Protocol):
    """One mechanism's answer to "may this call go out, and when?"."""

    def check(self) -> None:
        """Raise when this mechanism refuses outright rather than delaying."""
        ...

    def wait_seconds(self) -> float:
        """Seconds until this mechanism would permit a call; `0.0` when it does."""
        ...

    def stamp(self) -> None:
        """Record that a call is being made now."""
        ...


@dataclass(slots=True)
class AdmissionChain:
    """Every mechanism guarding one operation, asked in the source's own order."""

    mechanisms: tuple[AdmissionPolicy, ...]

    def check(self) -> None:
        """Let the first mechanism that refuses outright be the one that speaks."""
        for mechanism in self.mechanisms:
            mechanism.check()

    def wait_seconds(self) -> float:
        """The longest wait any mechanism asks for: the slowest gate governs."""
        return max((mechanism.wait_seconds() for mechanism in self.mechanisms), default=0.0)

    def stamp(self) -> None:
        """Tell every mechanism that this call happened. All of them count it."""
        for mechanism in self.mechanisms:
            mechanism.stamp()


def admission_for(policy: RateLimitPolicy, monotonic: Callable[[], float]) -> AdmissionChain:
    """Build the chain *policy* asks for, defaulting to the rolling windows."""
    if policy.admission != TOKEN_BUCKET:
        return AdmissionChain(
            (RollingWindows(policy.requests_per_minute, policy.requests_per_hour, monotonic),)
        )
    mechanisms: list[AdmissionPolicy] = [
        DailyQuota(policy.daily_quota, monotonic),
        TokenBucket(float(policy.burst_capacity), policy.requests_per_minute / 60.0, monotonic),
    ]
    if policy.dos_burst_limit:
        mechanisms.append(
            DosDetector(policy.dos_burst_limit, float(policy.dos_window_seconds), monotonic)
        )
    return AdmissionChain(tuple(mechanisms))
