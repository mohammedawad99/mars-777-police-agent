"""The one evaluation that is only ever allowed to happen once.

Everything here is built so that the interesting failures are refusals. The
sealed set may be judged **once**, against **one** frozen candidate, and the
result is historical evidence rather than a measurement that can be improved by
running it again - so the guard checks the seal, the candidate and the absence
of a prior result before anything is played, and publication refuses to
overwrite.

**Refusals, not warnings.** Each check raises. A one-shot evaluation that
printed a warning and continued would be a one-shot evaluation in name only.

**Atomic publication.** The result is written to a temporary file in the same
directory and then renamed, so an interrupted run leaves either nothing or a
complete record - never a half-written result that a later reader would treat
as the official one.
"""

import json
import os
from pathlib import Path
from typing import Any

RESULT_NAME = "final_holdout_result.json"
"""The single official result file. Its existence means the set is consumed."""


class SealMismatchError(Exception):
    """The sealed set or the candidate is not the one that was frozen."""


class AlreadyConsumedError(Exception):
    """This holdout has already been evaluated. It cannot be evaluated again."""


def guard(
    root: Path, expect_commitment: str, expect_candidate: str, actual_candidate: str
) -> dict[str, Any]:
    """Check the seal, the candidate and the absence of a result. Plays nothing."""
    if (root / "candidates" / RESULT_NAME).exists():
        raise AlreadyConsumedError(
            "a final-holdout result already exists; the set is consumed and may not be rerun"
        )
    document: dict[str, Any] = json.loads((root / "final_holdout.json").read_text(encoding="utf-8"))
    if document.get("results_present") is not False:
        raise SealMismatchError("the seal reports results already present")
    if document.get("commitment_sha256") != expect_commitment:
        raise SealMismatchError(
            "the sealed commitment does not match the frozen one; the set has changed"
        )
    if actual_candidate != expect_candidate:
        raise SealMismatchError(
            f"the candidate source no longer matches the frozen hash: {actual_candidate}"
        )
    return document


def publish(root: Path, document: dict[str, Any]) -> Path:
    """Write the official result atomically, refusing to replace one."""
    target = root / "candidates" / RESULT_NAME
    if target.exists():
        raise AlreadyConsumedError("a final-holdout result is already recorded")
    target.parent.mkdir(parents=True, exist_ok=True)
    staging = target.with_suffix(".tmp")
    staging.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(staging, target)
    return target


def run_once(root: Path, expect_commitment: str, expect_candidate: str) -> dict[str, Any]:
    """Judge the frozen candidate against the sealed set. Exactly once, ever.

    Both sides are played here, unlike validation and stress: the sealed set has
    no committed baseline rows, because playing it earlier is precisely what a
    holdout forbids.
    """
    from .candidates.registry import BUILDERS, CANDIDATES
    from .compare import by_group, compare
    from .identity import baseline_identity
    from .runner import Sweep
    from .sealed import sealed_set
    from .seeds import final_holdout_bank
    from .stats import paired_by_scenario

    entry = CANDIDATES["C4"]
    seal = guard(root, expect_commitment, expect_candidate, entry.source_sha256)
    identity = baseline_identity()
    enumerated = sealed_set(identity.role)
    if enumerated.commitment != expect_commitment:
        raise SealMismatchError("the enumerated scenarios do not reproduce the sealed commitment")
    bank = final_holdout_bank()
    print(f"final holdout: {len(enumerated.scenarios)} scenarios, both sides", flush=True)
    from .strategy_port import Policy

    baseline: Policy = _production_strategy()
    before = Sweep(identity, baseline, bank).run()
    after = Sweep(identity, BUILDERS["C4"](), bank).run()
    head = compare(before, after)
    interval = paired_by_scenario(
        {one.scenario_id: float(one.won) for one in before},
        {one.scenario_id: float(one.won) for one in after},
    )
    document = {
        "label": "FINAL HOLDOUT - ONE-SHOT RESULT - DO NOT RERUN",
        "commitment_sha256": seal["commitment_sha256"],
        "scenario_count": seal["count"],
        "seed_sha256": bank.digest,
        "baseline_strategy": identity.strategy,
        "baseline_sha256": identity.source_sha256,
        "candidate": entry.name,
        "revision": entry.revision,
        "candidate_sha256": entry.source_sha256,
        "overall": {
            **head.as_record(),
            **interval.as_record(),
            "delta": head.delta,
            "low": interval.low,
            "high": interval.high,
        },
        "family": _cells(before, after, "opponent_family", by_group),
        "config": _cells(before, after, "config", by_group),
        "legality_failures": 0,
    }
    return {"path": str(publish(root, document)), **document}


def _production_strategy() -> Any:
    """The shipped policy, read through the same accessor the benchmark uses."""
    from .bench_main import strategy

    return strategy()


def _cells(before: Any, after: Any, field: str, by_group: Any) -> dict[str, Any]:
    """Per-group paired records with their intervals."""
    from .stats import paired_by_scenario

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
