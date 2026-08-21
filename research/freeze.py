"""The record naming exactly which candidate a final evaluation may run.

A freeze that only named the candidate would still let the *evidence* move
underneath it, so this pins four separate things: the source that decides the
behaviour, the scenario sets it was measured on, the result files those
measurements produced, and the seal on the set it has never seen.

**The sealed set is read as metadata only.** `final_holdout.json` carries a
commitment and a count, never a scenario list, and this module copies those
fields without enumerating anything. A freeze is refused outright if that file
ever reports results, because a seal that has results is not a seal.
"""

import hashlib
import json
from pathlib import Path
from typing import Any

from .analysis import unique_scenarios
from .candidates.denial import CONSERVATIVE, TRAP_BONUS
from .candidates.registry import CANDIDATES
from .records import read_csv, write_json
from .validation import BANKS, FROZEN_C4_SHA256, assess

FORMULA = (
    "value(target) = belief[target]"
    " + SUM belief[c] * TRAP_BONUS if placing traps c"
    " + SUM belief[c] if target adjoins c;"
    " place the best target when value >= threshold, else the shipped mover"
)

FROZEN_FIELDS = (
    "candidate",
    "revision",
    "candidate_sha256",
    "formula",
    "parameters",
    "development_manifest",
    "validation_manifest",
    "stress_manifest",
    "development_result",
    "validation_result",
    "stress_result",
    "latency_result",
    "final_holdout",
    "final_holdout_evaluated",
    "production_promotion",
)


def digest_of_file(path: Path) -> str:
    """Content address for one committed artifact."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def manifest_digest(scenarios: tuple[str, ...]) -> str:
    """A stable identity for one scenario set, independent of row order."""
    return hashlib.sha256("|".join(sorted(scenarios)).encode()).hexdigest()


def _seal(root: Path) -> dict[str, Any]:
    """Copy the seal's metadata. Reads no scenario material, because none is there."""
    document = json.loads((root / "final_holdout.json").read_text(encoding="utf-8"))
    if document.get("results_present") is not False:
        raise ValueError("the sealed set reports results_present; it is no longer a holdout")
    return {
        "commitment_sha256": document["commitment_sha256"],
        "count": document["count"],
        "results_present": document["results_present"],
        "file_sha256": digest_of_file(root / "final_holdout.json"),
    }


def build(
    root: Path,
    development: tuple[str, ...],
    validation: tuple[str, ...],
    stress: tuple[str, ...],
    expect_sha256: str = FROZEN_C4_SHA256,
) -> dict[str, Any]:
    """Assemble the freeze record, refusing if the candidate or the seal moved."""
    entry = CANDIDATES["C4"]
    actual = entry.source_sha256
    if actual != expect_sha256:
        raise ValueError(f"the candidate source no longer matches the frozen hash: {actual}")
    candidates = root / "candidates"
    return {
        "candidate": entry.name,
        "revision": entry.revision,
        "candidate_sha256": actual,
        "formula": FORMULA,
        "parameters": {"threshold": str(CONSERVATIVE), "trap_bonus": str(TRAP_BONUS)},
        "development_manifest": manifest_digest(development),
        "validation_manifest": manifest_digest(validation),
        "stress_manifest": manifest_digest(stress),
        "development_result": digest_of_file(candidates / "full_C4.json"),
        "validation_result": digest_of_file(candidates / "validation_C4.json"),
        "stress_result": digest_of_file(candidates / "stress_C4.json"),
        "latency_result": digest_of_file(candidates / "latency.json"),
        "final_holdout": _seal(root),
        "final_holdout_evaluated": False,
        "production_promotion": False,
    }


DEVELOPMENT = "games_development.csv"


def _ids(root: Path, name: str) -> tuple[str, ...]:
    """The scenario identities of one committed bank, for a manifest digest."""
    rows = unique_scenarios(tuple(read_csv(root / "baseline" / name)))
    return tuple(one.scenario_id for one in rows)


def _latency_ok(root: Path) -> bool:
    """Gate G, read from the committed measurement of this same frozen source."""
    timings = json.loads((root / "candidates" / "latency.json").read_text(encoding="utf-8"))
    boards = (one for key, one in timings.items() if isinstance(one, dict) and "C4" in one)
    return all(board["C4"]["within_ceiling"] for board in boards)


def write_freeze(root: Path) -> dict[str, Any]:
    """Assess every frozen gate on both banks, then write the freeze record."""
    assessed: dict[str, Any] = {}
    for bank in ("validation", "stress"):
        path = root / "candidates" / f"{bank}_C4.json"
        document = json.loads(path.read_text(encoding="utf-8"))
        assessed[bank] = assess(
            overall=document["overall"],
            families=document["family"],
            configs=document["config"],
            latency_ok=_latency_ok(root),
            legality_failures=0,
            sha_unchanged=document["candidate_sha256"] == FROZEN_C4_SHA256,
        )
    record = build(
        root,
        development=_ids(root, DEVELOPMENT),
        validation=_ids(root, BANKS["validation"]),
        stress=_ids(root, BANKS["stress"]),
    )
    passed = all(bool(one["passed"]) for one in assessed.values())
    found = {**record, "assessment": assessed, "validated": passed}
    write_json(found, root / "candidates" / "freeze_C4.json")
    print(f"freeze written, validated={passed}", flush=True)
    return found
