"""Turning benchmark rows into the tables a reader can argue with.

Every number a figure or a report shows is computed here, in a tested function,
rather than in a notebook cell or a plotting call. That is the whole reason this
module exists: a statistic nobody can run twice is not evidence.

**The primary metric is the tournament's own.** A win is `own_score >
opponent_score` under Appendix F Table 17, and the capture/survival rates below
are counts of the outcomes the domain reported - not a research score invented
to make a candidate look better than the league would.

**The statistical unit is the scenario, not the row** (Stage 9B-0F). Policies
here are deterministic, so replaying a scenario produces the identical game;
counting it twice would inflate `N` without adding one bit of evidence. Every
aggregate therefore collapses rows by `scenario_id` first, and the bootstrap
resamples those unique scenarios.

**The fixed reference geometry is reported apart from the headline.** Its legal
opening space is exactly one, so it contributes seven scenarios in total - one
per opponent family - and folding seven observations in beside two thousand
would let a tiny cell borrow their confidence.
"""

from collections.abc import Callable
from dataclasses import dataclass

from .configs import corpus
from .records import GameRecord
from .stats import Estimate, estimate

Selector = Callable[[GameRecord], float]

PRIMARY = "win_rate"

REFERENCE_CONFIGS: tuple[str, ...] = tuple(one.name for one in corpus() if one.fixed_starts)
"""Configurations whose opening geometry is fixed, so their scenario space is one."""


def unique_scenarios(records: tuple[GameRecord, ...]) -> tuple[GameRecord, ...]:
    """One row per `scenario_id`, keeping the first in a deterministic order.

    Defensive rather than decorative: the sweep already emits one row per
    scenario, and this guarantees the property for any file that is loaded,
    merged or replayed later.
    """
    seen: dict[str, GameRecord] = {}
    for record in sorted(records, key=lambda one: (one.scenario_id, one.seed_set, one.seed)):
        seen.setdefault(record.scenario_id, record)
    return tuple(seen.values())


def headline(records: tuple[GameRecord, ...]) -> tuple[GameRecord, ...]:
    """The scenarios the primary aggregate is computed over: reference excluded."""
    return tuple(one for one in unique_scenarios(records) if one.config not in REFERENCE_CONFIGS)


def reference(records: tuple[GameRecord, ...]) -> tuple[GameRecord, ...]:
    """The fixed-geometry scenarios, reported on their own with their real `N`."""
    return tuple(one for one in unique_scenarios(records) if one.config in REFERENCE_CONFIGS)


def win(record: GameRecord) -> float:
    """The tournament outcome, as a zero-or-one for averaging."""
    return float(record.won)


def captured(record: GameRecord) -> float:
    """Whether this game ended in a capture, whichever side benefits."""
    return float(record.captured)


def survived(record: GameRecord) -> float:
    """Whether the thief reached the survival threshold."""
    return float(record.outcome == "SURVIVAL")


def steps(record: GameRecord) -> float:
    """How many full rounds the sub-game lasted."""
    return float(record.steps)


def barriers(record: GameRecord) -> float:
    """How many placements the police actually spent."""
    return float(record.barriers_placed)


def score(record: GameRecord) -> float:
    """The Appendix F points this role earned in this game."""
    return float(record.own_score)


METRICS: dict[str, Selector] = {
    PRIMARY: win,
    "capture_rate": captured,
    "survival_rate": survived,
    "mean_steps": steps,
    "mean_barriers": barriers,
    "mean_score": score,
}


@dataclass(frozen=True, slots=True)
class Cell:
    """One group of games and everything measured over it."""

    key: str
    group: str
    estimates: dict[str, Estimate]

    def as_row(self) -> dict[str, object]:
        """A flat table row: the group, then every metric's summary."""
        row: dict[str, object] = {"group_by": self.key, "group": self.group}
        for name, found in self.estimates.items():
            summary = found.as_record()
            row[name] = summary["mean"]
            row[f"{name}_ci_low"] = summary["ci_low"]
            row[f"{name}_ci_high"] = summary["ci_high"]
        row["n"] = next(iter(self.estimates.values())).n
        return row


def group_by(records: tuple[GameRecord, ...], key: str) -> dict[str, tuple[GameRecord, ...]]:
    """Split *records* by one attribute, in sorted key order for determinism."""
    found: dict[str, list[GameRecord]] = {}
    for record in records:
        found.setdefault(str(getattr(record, key)), []).append(record)
    return {name: tuple(found[name]) for name in sorted(found)}


def summarise(records: tuple[GameRecord, ...], key: str, group: str) -> Cell:
    """Every metric over one group, over **unique scenarios**, with honest intervals."""
    rows = unique_scenarios(records)
    return Cell(
        key=key,
        group=group,
        estimates={
            name: estimate(tuple(select(one) for one in rows), seed=len(rows))
            for name, select in METRICS.items()
        },
    )


def table(records: tuple[GameRecord, ...], key: str) -> tuple[Cell, ...]:
    """One row per distinct value of *key*, ordered so two runs agree."""
    grouped = group_by(unique_scenarios(records), key)
    return tuple(summarise(group, key, name) for name, group in grouped.items())


def overall(records: tuple[GameRecord, ...]) -> Cell:
    """The headline: unique scenarios, fixed reference geometry excluded."""
    return summarise(headline(records), "all", "all")


def reference_cell(records: tuple[GameRecord, ...]) -> Cell:
    """The reference geometry on its own, so its small `N` stays visible."""
    return summarise(reference(records), "reference", "appendixF-example")
