"""The daily quota manager: the last line before the provider blocks the account.

Ch 9 §9.3.1 names it as the first of the Gatekeeper's three cumulative
mechanisms: *"a counter that tracks the number of operations performed on a
given day and prevents crossing the daily safety threshold. This is the last
line against account blocking: if the quota is exhausted, no further request
goes out."*

**Exhaustion is a refusal, not a wait.** A bucket asks a caller to come back in
a moment; a spent daily quota has nothing to offer until the day turns, and
pretending otherwise would park a caller for hours. So this mechanism refuses,
and the caller is told which limit stopped it.

**The day is measured on the injected clock**, so a test can cross a boundary
without waiting for one and a wall-clock correction cannot silently reset the
allowance.
"""

from collections.abc import Callable
from dataclasses import dataclass, field

DAY_SECONDS = 86400.0


class QuotaExhaustedError(Exception):
    """The daily safety threshold for this operation is spent."""


@dataclass(slots=True)
class DailyQuota:
    """How many calls one operation may make in a rolling day, and how many are left."""

    limit: int
    monotonic: Callable[[], float]
    _stamps: list[float] = field(default_factory=list)

    def __post_init__(self) -> None:
        if type(self.limit) is not int or self.limit <= 0:
            raise ValueError("a daily quota must permit at least one call")

    def _trim(self) -> float:
        now = self.monotonic()
        self._stamps = [stamp for stamp in self._stamps if now - stamp < DAY_SECONDS]
        return now

    @property
    def spent(self) -> int:
        """How many calls this operation has made in the last day."""
        self._trim()
        return len(self._stamps)

    @property
    def remaining(self) -> int:
        """How many calls are still permitted today."""
        return max(0, self.limit - self.spent)

    def check(self) -> None:
        """Refuse outright when the day's allowance is gone."""
        if self.remaining <= 0:
            raise QuotaExhaustedError(
                f"the daily quota of {self.limit} is spent; no further call goes out today"
            )

    def wait_seconds(self) -> float:
        """A quota never asks a caller to wait: it either permits or refuses."""
        return 0.0

    def stamp(self) -> None:
        """Record that one of today's calls has been made.

        The instant is taken **before** the list is touched: `_trim` rebinds
        `_stamps`, so appending to the expression evaluated first would append
        to the list that was just replaced and lose the call.
        """
        now = self._trim()
        self._stamps.append(now)
