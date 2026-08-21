"""Evaluating one already-frozen candidate on a bank it was never tuned on.

**The candidate is checked before it is run.** `evaluate` refuses unless the
candidate's source hash still equals the hash its development evidence was
produced with. That is what stops a stage from quietly re-freezing a candidate
it has just watched fail: if C4 fails, C4 fails.

**Only banks that were never sealed.** `BANKS` names the two working banks and
there is no argument, flag or fallback that reaches the sealed set - not because
a caller is trusted to avoid it, but because the name does not exist here.

The baseline side is not replayed: the committed result rows *are* the frozen
strategy's play on exactly these scenarios, and re-running them would only add a
chance of drift to a comparison whose whole point is that both sides met
identical conditions.
"""

from pathlib import Path
from typing import Any

from .analysis import unique_scenarios
from .candidates.registry import CANDIDATES
from .compare import by_group, compare, replay_all
from .gates import Cell, material_regression, overall_passes
from .records import GameRecord, read_csv, write_csv, write_json
from .stats import paired_by_scenario

BANKS: dict[str, str] = {"validation": "games_holdout.csv", "stress": "games_stress.csv"}
"""Bank name to committed result file. The sealed bank is absent by design; its
label was kept as `holdout` in Stage 9B-0F so committed rows still load."""

FROZEN_C4_SHA256 = "1cc0a20d40680874a337dd3f7f2e552924763e42f291066990cb0dc8385c2884"
"""The C4 source hash the Stage-9B-1A development evidence was produced with."""

LABEL = "RESEARCH EVIDENCE - NOT FINAL HOLDOUT - NOT YET PRODUCTION"


def frozen_source_sha256() -> str:
    """C4's source hash as it is on disk right now."""
    return CANDIDATES["C4"].source_sha256


def _cells(groups: dict[str, Any]) -> dict[str, Cell]:
    return {
        name: Cell(
            group=name,
            n=int(one["n"]),
            delta=float(one["delta"]),
            low=None if one["low"] is None else float(one["low"]),
            high=None if one["high"] is None else float(one["high"]),
        )
        for name, one in groups.items()
    }


def assess(
    overall: dict[str, Any],
    families: dict[str, Any],
    configs: dict[str, Any],
    latency_ok: bool,
    legality_failures: int,
    sha_unchanged: bool,
) -> dict[str, Any]:
    """Apply every frozen gate and report each one, not just the conclusion."""
    head = _cells({"overall": overall})["overall"]
    family_cells, config_cells = _cells(families), _cells(configs)
    bad = sorted(
        name for name, cell in {**family_cells, **config_cells}.items() if material_regression(cell)
    )
    gates = {
        "A_zero_legality_failures": legality_failures == 0,
        "C_positive_delta": head.delta > 0.0,
        "D_lower_bound_above_zero": overall_passes(head),
        "E_no_material_family_regression": not any(
            material_regression(one) for one in family_cells.values()
        ),
        "F_no_material_config_regression": not any(
            material_regression(one) for one in config_cells.values()
        ),
        "G_latency_within_ceiling": latency_ok,
        "I_candidate_hash_unchanged": sha_unchanged,
    }
    return {"gates": gates, "passed": all(gates.values()), "material_regressions": bad}


def _grouped(
    before: tuple[GameRecord, ...], after: tuple[GameRecord, ...], field: str
) -> dict[str, Any]:
    left = {one.scenario_id: float(one.won) for one in before}
    right = {one.scenario_id: float(one.won) for one in after}
    found: dict[str, Any] = {}
    for name, cell in by_group(before, after, field).items():
        keys = {one.scenario_id for one in before if getattr(one, field) == name}
        interval = paired_by_scenario(
            {k: v for k, v in left.items() if k in keys},
            {k: v for k, v in right.items() if k in keys},
        )
        found[name] = {
            **cell.as_record(),
            **interval.as_record(),
            "delta": cell.delta,
            "low": interval.low,
            "high": interval.high,
        }
    return found


def evaluate(root: Path, bank: str, expect_sha256: str) -> dict[str, Any]:
    """Replay the frozen candidate over *bank*, paired on identical scenarios."""
    if bank not in BANKS:
        raise ValueError(f"unknown bank {bank!r}")
    actual = frozen_source_sha256()
    if actual != expect_sha256:
        raise ValueError(f"the candidate source no longer matches the frozen hash: {actual}")
    rows = unique_scenarios(tuple(read_csv(root / "baseline" / BANKS[bank])))
    print(f"{bank} C4 over {len(rows)} scenarios", flush=True)
    played = (
        replay_all(CANDIDATES["C4"].name, rows)
        if False
        else replay_all(
            __import__("research.candidates.registry", fromlist=["BUILDERS"]).BUILDERS["C4"](),
            rows,
            (CANDIDATES["C4"].name, actual),
        )
    )
    write_csv(played, root / "candidates" / f"{bank}_C4.csv")
    left = {one.scenario_id: float(one.won) for one in rows}
    right = {one.scenario_id: float(one.won) for one in played}
    interval = paired_by_scenario(left, right)
    head = compare(rows, played)
    found: dict[str, Any] = {
        "label": LABEL,
        "bank": bank,
        "candidate": CANDIDATES["C4"].name,
        "revision": CANDIDATES["C4"].revision,
        "candidate_sha256": actual,
        "overall": {
            **head.as_record(),
            **interval.as_record(),
            "delta": head.delta,
            "low": interval.low,
            "high": interval.high,
        },
        "family": _grouped(rows, played, "opponent_family"),
        "config": _grouped(rows, played, "config"),
    }
    write_json(found, root / "candidates" / f"{bank}_C4.json")
    return found
