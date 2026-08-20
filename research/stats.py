"""The statistics a promotion may rest on, and the ones it may not.

Two rules shape this module. **No promotion from an average alone**: a
proportion is reported with its sample size and an interval, so a reader can see
whether a difference is evidence or noise. **No overstated significance**: a
tiny sample is refused rather than decorated with an interval that means
nothing.

**The interval is a deterministic bootstrap.** Resamples are drawn from a
SHA-256 counter rather than a random module, so the same data always yields the
same interval on any machine - which is what makes a published figure
reproducible and an argument about it checkable.

**The resampling unit is one independent observation, and `analysis` is what
guarantees that.** These functions resample whatever list they are handed, so
handing them duplicate rows would inflate confidence rather than measure it;
every caller collapses rows by `scenario_id` first, and a test asserts that
duplicating a series does not narrow its interval.
"""

import hashlib
from dataclasses import dataclass
from statistics import median

MIN_SAMPLE = 8
"""Below this, an interval would be theatre. Reported as absent, never faked."""

RESAMPLES = 1000
CONFIDENCE = 0.95


class SmallSampleError(Exception):
    """Too few observations for the interval that was asked for."""


@dataclass(frozen=True, slots=True)
class Estimate:
    """One measured quantity: its centre, its spread, and how much data it had."""

    n: int
    mean: float
    median: float
    low: float | None
    high: float | None

    def as_record(self) -> dict[str, object]:
        """Flat, rounded output for a table. Rounding is display, not arithmetic."""
        return {
            "n": self.n,
            "mean": round(self.mean, 6),
            "median": round(self.median, 6),
            "ci_low": None if self.low is None else round(self.low, 6),
            "ci_high": None if self.high is None else round(self.high, 6),
        }


def _draw(seed: int, index: int, size: int) -> int:
    material = f"bootstrap/{seed}/{index}".encode()
    return int.from_bytes(hashlib.sha256(material).digest()[:8], "big") % size


def bootstrap_interval(values: tuple[float, ...], seed: int = 0) -> tuple[float, float]:
    """A deterministic percentile bootstrap interval for the mean of *values*."""
    if len(values) < MIN_SAMPLE:
        raise SmallSampleError(f"an interval needs at least {MIN_SAMPLE} observations")
    size = len(values)
    means = []
    for round_index in range(RESAMPLES):
        total = 0.0
        for position in range(size):
            total += values[_draw(seed, round_index * size + position, size)]
        means.append(total / size)
    means.sort()
    tail = (1.0 - CONFIDENCE) / 2.0
    return (means[int(tail * RESAMPLES)], means[min(int((1.0 - tail) * RESAMPLES), RESAMPLES - 1)])


def estimate(values: tuple[float, ...], seed: int = 0) -> Estimate:
    """Summarise *values*, with an interval only when the sample supports one."""
    if not values:
        raise SmallSampleError("an estimate needs at least one observation")
    low: float | None = None
    high: float | None = None
    if len(values) >= MIN_SAMPLE:
        low, high = bootstrap_interval(values, seed)
    return Estimate(len(values), sum(values) / len(values), median(values), low, high)


def paired_difference(
    before: tuple[float, ...], after: tuple[float, ...], seed: int = 0
) -> Estimate:
    """The per-observation difference, which is what a paired comparison compares.

    Refused unless the two series are the same length: a paired comparison whose
    pairs do not line up is not a paired comparison.
    """
    if len(before) != len(after):
        raise SmallSampleError("a paired comparison needs the same games on both sides")
    return estimate(tuple(right - left for left, right in zip(before, after, strict=True)), seed)


def paired_by_scenario(
    before: dict[str, float], after: dict[str, float], seed: int = 0
) -> Estimate:
    """The paired difference over the scenarios both sides actually played.

    Keyed by `scenario_id` rather than by position, because a baseline measured
    on one seed set and a candidate on another are not pairs however neatly
    their lists line up. A scenario only one side played is refused rather than
    dropped silently: a comparison over a subset nobody chose is not the
    comparison that was asked for.
    """
    if set(before) != set(after):
        raise SmallSampleError(
            "a paired comparison needs the same scenario set on both sides;"
            f" {len(set(before) ^ set(after))} scenario(s) appear on only one"
        )
    keys = sorted(before)
    return paired_difference(
        tuple(before[one] for one in keys), tuple(after[one] for one in keys), seed
    )
