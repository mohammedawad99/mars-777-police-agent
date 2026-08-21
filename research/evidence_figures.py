"""Figures for the validation and stress evidence, and the whole search so far.

Kept apart from `candidate_tables`, which draws the development screening: these
read result documents rather than a screening document, and the two would not
fit one module inside the line budget.

Every figure says on its face which bank it came from, because a delta means
something different on the set that selected the candidate than on a set the
candidate had never seen.
"""

import json
from pathlib import Path
from typing import Any

from mars777_police.gui.primitives import Frame

from .charts import save
from .curve import Point, progression
from .delta_chart import Delta, diverging

LABEL = "STRATEGY RESEARCH EVIDENCE - one-shot final holdout shown once, never re-estimated"

STATUS = {"C1": "REJECTED_GATE", "C2": "NOT_ADVANCED", "C3": "REJECTED_GATE", "C4": "ADVANCED"}
SHORT = {
    "development": "C4 dev",
    "validation": "C4 val",
    "stress": "C4 stress",
    "final_holdout": "C4 HOLDOUT",
}
FINAL_NAME = "final_holdout_result.json"
"""The one-shot result. Read, never recomputed: it is shown once."""


def _load(path: Path) -> dict[str, Any]:
    """Any committed research document, as written."""
    document: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    return document


def _read(path: Path) -> dict[str, Any]:
    """Read one *result* document, in either shape it has been written in.

    Stage 9B-1A wrote the overall row as `win_delta` beside a separate
    `paired_ci`; Stage 9B-1B folds the interval into the row. Rather than
    rewrite a frozen measurement to match a newer layout - which would change
    its digest for a cosmetic reason - both shapes are read here.
    """
    document = _load(path)
    overall = dict(document["overall"])
    if "delta" not in overall:
        interval = document.get("paired_ci", {})
        overall["delta"] = overall["win_delta"]
        overall["ci_low"], overall["ci_high"] = interval.get("ci_low"), interval.get("ci_high")
    document["overall"] = overall
    return document


def _delta(name: str, cell: dict[str, Any], kept: bool = True) -> Delta:
    return Delta(
        name,
        float(cell["delta"]),
        None if cell["ci_low"] is None else float(cell["ci_low"]),
        None if cell["ci_high"] is None else float(cell["ci_high"]),
        int(cell["n"]),
        kept,
    )


def family_figure(document: dict[str, Any], bank: str) -> Frame:
    """Every opponent family's paired delta on one bank, worst first."""
    cells = sorted(document["family"].items(), key=lambda one: one[1]["delta"])
    bars = tuple(_delta(name, cell, cell["delta"] >= 0.0) for name, cell in cells)
    return diverging(
        f"C4 on {bank.upper()}: paired win-rate change by opponent family",
        "win-rate delta with 95% paired interval",
        bars,
        f"{LABEL}. Paired on identical scenario_ids, N={document['overall']['n']}.",
    )


def bank_figure(documents: dict[str, dict[str, Any]]) -> Frame:
    """Development against validation against stress, on one axis."""
    bars = tuple(_delta(name, one["overall"]) for name, one in documents.items())
    return diverging(
        "C4: the same frozen candidate on three independent banks",
        "overall paired win-rate delta with 95% interval",
        bars,
        f"{LABEL}. Identical source hash on every bank.",
    )


def search_figure(screening: dict[str, Any], documents: dict[str, dict[str, Any]]) -> Frame:
    """The whole strategy research progression, rejected candidates included."""
    points = [
        Point(f"{key} screen", float(screening[key]["paired_ci"]["mean"]), STATUS[key])
        for key in ("C1", "C2", "C3", "C4")
        if key in screening
    ]
    points += [
        Point(
            SHORT[name],
            float(one["overall"]["delta"]),
            "PROMOTED" if name == "final_holdout" else "VALIDATED",
        )
        for name, one in documents.items()
    ]
    return progression(
        "Strategy research progression (order evaluated, not training)",
        "paired win-rate delta vs frozen baseline",
        tuple(points),
        f"{LABEL}. No model is trained; each point is a separate replayed evaluation.",
    )


def write_all(root: Path) -> tuple[Path, ...]:
    """Redraw every evidence figure from the committed results.

    The final-holdout point is read from its recorded one-shot result. It is
    never re-estimated, and no figure recomputes it.
    """
    documents = {
        name: _read(root / "candidates" / f"{name}_C4.json") for name in ("validation", "stress")
    }
    documents = {"development": _read(root / "candidates" / "full_C4.json"), **documents}
    final = root / "candidates" / FINAL_NAME
    if final.exists():
        documents["final_holdout"] = _read(final)
    out = root / "figures" / "candidates"
    written = [
        save(bank_figure(documents), out / "c4_by_bank.png"),
        save(
            search_figure(_load(root / "candidates" / "screening.json"), documents),
            out / "strategy_research_progression.png",
        ),
    ]
    for name in ("validation", "stress", "final_holdout"):
        if name in documents:
            written.append(
                save(family_figure(documents[name], name), out / f"c4_{name}_family.png")
            )
    return tuple(written)
