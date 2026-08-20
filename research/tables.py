"""Every committed table and figure, regenerated from the committed result rows.

One function writes them all, so "regenerate the evidence" is a single call and
nothing is produced by hand. The inputs are result files; the outputs are CSV a
grader can open, JSON a script can read, and PNGs a report can show.
"""

import csv
from pathlib import Path

from .analysis import PRIMARY, Cell, overall, table
from .charts import Bar, bar_chart, save
from .identity import baseline_identity
from .records import GameRecord, write_json

GROUPS = ("opponent_family", "config", "grid", "seed_set")
FIGURES = ((PRIMARY, "win rate"), ("capture_rate", "capture rate"))


def write_rows(cells: tuple[Cell, ...], path: Path) -> Path:
    """Write one grouped table as deterministic CSV."""
    rows = [one.as_row() for one in cells]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    return path


def _bars(cells: tuple[Cell, ...], metric: str) -> tuple[Bar, ...]:
    return tuple(
        Bar(
            one.group,
            one.estimates[metric].mean,
            one.estimates[metric].low,
            one.estimates[metric].high,
            one.estimates[metric].n,
        )
        for one in cells
    )


def write_all(records: tuple[GameRecord, ...], root: Path) -> None:
    """Regenerate every table, summary and figure this stage commits."""
    identity = baseline_identity()
    caption = f"{identity.role} baseline {identity.strategy} @ {identity.commit[:12]}"
    figures = root / "figures"
    for key in GROUPS:
        cells = table(records, key)
        write_rows(cells, root / "tables" / f"by_{key}.csv")
        for metric, unit in FIGURES:
            frame = bar_chart(
                f"{identity.role} {metric} by {key}", unit, _bars(cells, metric), caption
            )
            save(frame, figures / f"{metric}_by_{key}.png")
    summary = overall(records)
    write_json(
        {
            "games": len(records),
            "baseline": identity.as_record(),
            "overall": {name: found.as_record() for name, found in summary.estimates.items()},
        },
        root / "tables" / "overall.json",
    )
