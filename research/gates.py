"""The promotion gates, and the vocabulary a verdict is allowed to use.

Every rule here was frozen in `docs/research/COMPETITIVE_RESEARCH.md` §9 before
any candidate existed, and this module is deliberately the only place they are
written as code - a gate restated at each call site is a gate that drifts.

**Three statuses, not two.** Stage 9B-1A wrote a binary verdict, so C2 - which
beat the baseline by +0.0510 and lost the *selection* to a better candidate -
was recorded with the same word as C1, which lost every game it had won. Those
are different research outcomes and a reader cannot recover the difference from
the number alone, so the vocabulary now separates them.
"""

from dataclasses import dataclass

MATERIAL_DROP = 0.05
"""More than five percentage points. Frozen in §9 before any candidate ran."""

ADVANCED = "ADVANCED"
"""Passed its gates and was selected to continue."""

NOT_ADVANCED = "NOT_ADVANCED"
"""Passed its gates; another candidate was selected instead."""

REJECTED_GATE = "REJECTED_GATE"
"""Failed a frozen gate on its own evidence."""

STATUSES = (ADVANCED, NOT_ADVANCED, REJECTED_GATE)


@dataclass(frozen=True, slots=True)
class Cell:
    """One measured group: its paired difference and the interval around it."""

    group: str
    n: int
    delta: float
    low: float | None
    high: float | None

    def as_record(self) -> dict[str, object]:
        """Flat output for a table."""
        return {
            "group": self.group,
            "n": self.n,
            "delta": round(self.delta, 6),
            "ci_low": None if self.low is None else round(self.low, 6),
            "ci_high": None if self.high is None else round(self.high, 6),
            "material_regression": material_regression(self),
        }


def material_regression(cell: Cell) -> bool:
    """A drop of **more than** `MATERIAL_DROP` whose interval excludes zero.

    Both halves are required. A large drop whose interval still contains zero is
    noise the sample cannot separate, and a cell too small to carry an interval
    carries no evidence to convict on either - so it is reported, not condemned.
    """
    if cell.low is None or cell.high is None:
        return False
    return cell.delta < -MATERIAL_DROP and cell.high < 0.0


def overall_passes(cell: Cell) -> bool:
    """Gates C and D: a positive paired delta whose 95% lower bound clears zero."""
    if cell.low is None:
        return False
    return cell.delta > 0.0 and cell.low > 0.0


def verdict_for(passed_gates: bool, selected: bool) -> str:
    """The status word for one candidate, in the frozen three-value vocabulary."""
    if selected and not passed_gates:
        raise ValueError("a candidate that failed a gate cannot be selected")
    if selected:
        return ADVANCED
    return NOT_ADVANCED if passed_gates else REJECTED_GATE
