"""`python -m research.candidate_main` - screen candidates, then run the winner.

    uv run python -m research.candidate_main screen --out results
    uv run python -m research.candidate_main full --candidate C4 --out results
    uv run python -m research.candidate_main latency --out results
    uv run python -m research.candidate_main belief --out results
    uv run python -m research.candidate_main figures|evidence --out results
    uv run python -m research.candidate_main validation|stress|freeze --out results

**Never the sealed set.** The screening and full actions read
`games_development.csv`; the validation and stress actions read their own
committed banks, added at Stage 9B-1B once C4 was frozen. No action, flag or
fallback here reaches the sealed final holdout - the name does not appear in
this module's code, and `research.validation.BANKS` does not contain it.
"""

import argparse
from pathlib import Path

from .analysis import unique_scenarios
from .candidate_tables import write_all
from .candidates.registry import BUILDERS, CANDIDATES
from .compare import by_group, compare, replay_all
from .configs import corpus
from .diagnostics import write_belief
from .evidence_figures import write_all as write_evidence
from .freeze import write_freeze
from .latency import measure
from .records import GameRecord, read_csv, write_csv, write_json
from .screening import SHARE_PER_MILLE, VERSION, digest_of, screened
from .stats import paired_by_scenario
from .validation import FROZEN_C4_SHA256, evaluate

DEVELOPMENT = "games_development.csv"
LABEL = "DEVELOPMENT RESEARCH - not final holdout, not a production promotion"
CEILING_MS = 25.0
"""The per-decision ceiling frozen in Stage 9B-0, not re-negotiated here."""
TIMED = (1, 2)
"""`grid9`, because the committed baseline number was measured there and a
comparison needs the same board; and `grid11`, because the largest legal board
is the worst case and a ceiling that only holds on the smallest board holds
nothing."""


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Read the command line. Reaches no file and plays no game."""
    parser = argparse.ArgumentParser(prog="python -m research.candidate_main")
    parser.add_argument(
        "action",
        choices=(
            "screen",
            "full",
            "latency",
            "belief",
            "figures",
            "validation",
            "stress",
            "freeze",
            "evidence",
        ),
    )
    parser.add_argument("--out", type=Path, default=Path("results"))
    parser.add_argument("--candidate", default="C4")
    return parser.parse_args(argv)


def _identity(key: str) -> tuple[str, str]:
    """The name and source hash a candidate's own result rows must carry."""
    entry = CANDIDATES[key]
    return (entry.name, entry.source_sha256)


def development(root: Path) -> tuple[GameRecord, ...]:
    """The frozen baseline rows this stage is allowed to compare against."""
    return unique_scenarios(tuple(read_csv(root / "baseline" / DEVELOPMENT)))


def _summary(before: tuple[GameRecord, ...], after: tuple[GameRecord, ...]) -> dict[str, object]:
    left = {one.scenario_id: float(one.won) for one in before}
    right = {one.scenario_id: float(one.won) for one in after}
    interval = paired_by_scenario(left, right)
    return {
        "overall": compare(before, after).as_record(),
        "paired_ci": interval.as_record(),
        "family": {
            name: cell.as_record()
            for name, cell in by_group(before, after, "opponent_family").items()
        },
        "config": {
            name: cell.as_record() for name, cell in by_group(before, after, "config").items()
        },
    }


def screen(root: Path) -> dict[str, object]:
    """Replay every candidate over the frozen screening subset and record it."""
    rows = development(root)
    subset = tuple(one for one in rows if screened(one.scenario_id))
    found: dict[str, object] = {
        "label": LABEL,
        "screening": {
            "version": VERSION,
            "share_per_mille": SHARE_PER_MILLE,
            "n": len(subset),
            "digest": digest_of(tuple(one.scenario_id for one in rows)),
        },
    }
    for key in sorted(BUILDERS):
        print(f"screening {key} over {len(subset)} scenarios", flush=True)
        played = replay_all(BUILDERS[key](), subset, _identity(key))
        write_csv(played, root / "candidates" / f"screen_{key}.csv")
        found[key] = {**CANDIDATES[key].as_record(), **_summary(subset, played)}
    write_json(found, root / "candidates" / "screening.json")
    return found


def full(root: Path, key: str) -> dict[str, object]:
    """Replay one advancing candidate over the whole development set."""
    if key not in BUILDERS:
        raise SystemExit(f"unknown candidate {key!r}")
    rows = development(root)
    print(f"full development {key} over {len(rows)} scenarios", flush=True)
    played = replay_all(BUILDERS[key](), rows, _identity(key))
    write_csv(played, root / "candidates" / f"full_{key}.csv")
    found = {"label": LABEL, **CANDIDATES[key].as_record(), **_summary(rows, played)}
    write_json(found, root / "candidates" / f"full_{key}.json")
    return found


def latency(root: Path) -> dict[str, object]:
    """Time every candidate's decision against the frozen ceiling.

    A candidate that wins more games but misses the deadline has not improved
    anything, so this is measured for the rejected candidates too.
    """
    found: dict[str, object] = {"label": LABEL, "ceiling_ms": CEILING_MS}
    for index in TIMED:
        config = corpus()[index]
        board: dict[str, object] = {}
        for key in sorted(BUILDERS):
            timing = measure(BUILDERS[key](), config, seed=90001)
            print(f"{config.name} {key} p95 {timing.p95_ms:.3f} ms", flush=True)
            board[key] = {**timing.as_record(), "within_ceiling": timing.p95_ms <= CEILING_MS}
        found[config.name] = board
    write_json(found, root / "candidates" / "latency.json")
    return found


def main(argv: list[str] | None = None) -> int:
    """Run the requested action. Returns the process status."""
    arguments = parse_args(argv)
    if arguments.action == "screen":
        screen(arguments.out)
    elif arguments.action == "latency":
        latency(arguments.out)
    elif arguments.action == "belief":
        write_belief(arguments.out)
    elif arguments.action == "figures":
        write_all(arguments.out / "candidates" / "screening.json", arguments.out)
    elif arguments.action == "evidence":
        write_evidence(arguments.out)
    elif arguments.action in ("validation", "stress"):
        evaluate(arguments.out, arguments.action, FROZEN_C4_SHA256)
    elif arguments.action == "freeze":
        write_freeze(arguments.out)
    else:
        full(arguments.out, arguments.candidate)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
