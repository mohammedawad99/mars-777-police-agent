"""The committed candidate evidence, regenerated from the committed result files.

Inputs are the JSON written by `research.candidate_main`; outputs are a CSV a
grader can open and PNGs a report can show. Nothing is drawn by hand, and every
candidate that was tried appears in every artifact - including the two that lost,
because a figure showing only the survivors would misrepresent the search.
"""

import csv
import json
from pathlib import Path
from typing import Any

from mars777_police.gui.primitives import Frame

from .charts import save
from .curve import Point, progression
from .delta_chart import Delta, diverging

LABEL = "DEVELOPMENT RESEARCH / NOT FINAL HOLDOUT / NOT PRODUCTION PROMOTION"
ORDER = ("C1", "C2", "C3", "C4")
KEPT = ("C4",)
FIELDS = (
    "candidate",
    "revision",
    "summary",
    "n",
    "baseline_wins",
    "candidate_wins",
    "gains",
    "losses",
    "delta",
    "ci_low",
    "ci_high",
    "verdict",
)


def _maybe(value: Any) -> float | None:
    """A bootstrap declines below its minimum sample; that is not a zero."""
    return None if value is None else float(value)


def _read(path: Path) -> dict[str, Any]:
    """The one place untyped JSON crosses into typed code."""
    document: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    return document


def _cell(key: str, entry: dict[str, Any]) -> dict[str, Any]:
    overall = entry["overall"]
    interval = entry["paired_ci"]
    return {
        "candidate": key,
        "revision": entry.get("revision", ""),
        "summary": entry.get("summary", ""),
        "n": overall["n"],
        "baseline_wins": overall["baseline_wins"],
        "candidate_wins": overall["candidate_wins"],
        "gains": overall["gains"],
        "losses": overall["losses"],
        "delta": interval["mean"],
        "ci_low": interval["ci_low"],
        "ci_high": interval["ci_high"],
        "verdict": "advanced" if key in KEPT else "rejected",
    }


def screening_rows(document: dict[str, Any]) -> tuple[dict[str, Any], ...]:
    """One row per candidate, in the order the candidates were tried."""
    return tuple(_cell(key, document[key]) for key in ORDER if key in document)


def write_rows(rows: tuple[dict[str, Any], ...], path: Path) -> Path:
    """Deterministic CSV, same bytes on every platform."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(FIELDS), lineterminator="\n")
        writer.writeheader()
        writer.writerows([{key: row[key] for key in FIELDS} for row in rows])
    return path


def delta_figure(rows: tuple[dict[str, Any], ...], n: int) -> Frame:
    """Paired win-rate change per candidate, drawn around a real zero line."""
    bars = tuple(
        Delta(
            str(row["candidate"]),
            float(row["delta"]),
            _maybe(row["ci_low"]),
            _maybe(row["ci_high"]),
            int(row["n"]),
            str(row["verdict"]) == "advanced",
        )
        for row in rows
    )
    return diverging(
        "Police candidates: paired win-rate change vs frozen baseline",
        "win-rate delta with 95% paired interval",
        bars,
        f"{LABEL}. Screening subset, N={n} unique scenarios, same scenarios both sides.",
    )


def progression_figure(rows: tuple[dict[str, Any], ...]) -> Frame:
    """The search itself, in the order it happened, losers included."""
    points = tuple(
        Point(
            str(row["candidate"]),
            float(row["delta"]),
            str(row["verdict"]) == "advanced",
        )
        for row in rows
    )
    return progression(
        "Police candidate exploration progression (order tried, not training)",
        "win-rate delta vs frozen baseline",
        points,
        f"{LABEL}. No model is trained; each point is a separate replayed candidate.",
    )


def write_all(source: Path, out: Path) -> tuple[Path, ...]:
    """Regenerate every candidate table and figure from `screening.json`."""
    document = _read(source)
    rows = screening_rows(document)
    n = int(document["screening"]["n"])
    figures = out / "figures" / "candidates"
    return (
        write_rows(rows, out / "tables" / "candidates" / "screening.csv"),
        save(delta_figure(rows, n), figures / "candidate_delta.png"),
        save(progression_figure(rows), figures / "exploration_progression.png"),
    )
