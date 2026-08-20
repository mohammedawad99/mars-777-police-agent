"""The two rolling windows a provider operation's rate is measured over.

The guideline's own configuration names both a per-minute and a per-hour limit,
so both are kept: a burst that satisfies the minute can still exhaust the hour,
and a gate that only watched the faster window would let it.

**Rolling, and monotonic.** The windows slide over the calls actually made
rather than resetting on a fixed boundary, which is what stops a caller
double-spending across a boundary; and the clock is monotonic, because wall time
can move backwards and an interval measured against it can be negative.
"""

from collections.abc import Callable
from dataclasses import dataclass, field

MINUTE = 60.0
HOUR = 3600.0


@dataclass(slots=True)
class RollingWindows:
    """The recent call times of one operation, and when the next one may run."""

    per_minute: int
    per_hour: int
    monotonic: Callable[[], float]
    _stamps: list[float] = field(default_factory=list)

    def _trim(self, now: float) -> None:
        self._stamps = [stamp for stamp in self._stamps if now - stamp < HOUR]

    def check(self) -> None:
        """A window refuses nothing outright; it only ever asks a caller to wait."""

    def wait_seconds(self) -> float:
        """Seconds until a call may run: `0.0` when one may run right now."""
        now = self.monotonic()
        self._trim(now)
        waits = [0.0]
        minute = [stamp for stamp in self._stamps if now - stamp < MINUTE]
        if len(minute) >= self.per_minute:
            waits.append(minute[-self.per_minute] + MINUTE - now)
        if len(self._stamps) >= self.per_hour:
            waits.append(self._stamps[-self.per_hour] + HOUR - now)
        return max(waits)

    def stamp(self) -> None:
        """Record that a call is being made now."""
        now = self.monotonic()
        self._trim(now)
        self._stamps.append(now)
