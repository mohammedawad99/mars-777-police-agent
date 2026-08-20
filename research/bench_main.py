"""`python -m research.bench_main` - run the benchmark, analyse it, draw it.

One documented path from a frozen strategy to committed evidence:

    uv run python -m research.bench_main all --out results

There is no network here, no credential, no provider and no live game. Results
are written under the chosen root and never into the official artifact
namespace.

**The sealed final holdout is not reachable from any command here.** `working_banks`
is the only source of banks this module iterates, and the sealed bank is not in
it; there is deliberately no `--final-holdout` flag yet. Exactly one promotion
evaluation may run on it, in a later stage, after a candidate has been frozen -
and a flag that existed today would be a flag somebody could pass today.
"""

import argparse
from pathlib import Path

from mars777_police.app.competitive_strategy import CompetitiveStrategy

from . import tables
from .configs import corpus
from .identity import baseline_identity
from .latency import measure
from .manifest import manifest
from .records import GameRecord, read_csv, write_csv, write_json
from .runner import Sweep, size_of
from .sealed import sealed_set
from .seeds import FINAL_HOLDOUT, working_banks

BASELINE = "baseline"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Read the command line. This runs nothing and writes nothing."""
    parser = argparse.ArgumentParser(prog="python -m research.bench_main")
    parser.add_argument("action", choices=("bench", "analyse", "all"))
    parser.add_argument("--out", type=Path, default=Path("results"))
    parser.add_argument("--sets", nargs="*", default=None, help="seed banks to run")
    return parser.parse_args(argv)


def strategy() -> CompetitiveStrategy:
    """The production policy, constructed exactly as composition constructs it."""
    return CompetitiveStrategy()


def bench(root: Path, chosen: list[str] | None) -> tuple[GameRecord, ...]:
    """Play every selected seed bank against the whole corpus and record it."""
    identity = baseline_identity()
    if chosen and FINAL_HOLDOUT in chosen:
        raise SystemExit(
            f"{FINAL_HOLDOUT} is sealed: it is evaluated exactly once, after a candidate"
            " is frozen, in a later stage"
        )
    played: list[GameRecord] = []
    for bank in working_banks():
        if chosen and bank.name not in chosen:
            continue
        print(f"running {bank.name}: {size_of(bank)} games", flush=True)
        records = Sweep(identity, strategy(), bank).run()
        write_csv(records, root / BASELINE / f"games_{bank.name}.csv")
        played.extend(records)
    return tuple(played)


def load(root: Path) -> tuple[GameRecord, ...]:
    """Read every benchmark file back, so analysis never depends on a live run."""
    found: list[GameRecord] = []
    for path in sorted((root / BASELINE).glob("games_*.csv")):
        found.extend(read_csv(path))
    if not found:
        raise SystemExit(f"no benchmark records under {root / BASELINE}")
    return tuple(found)


def analyse(root: Path) -> None:
    """Regenerate every table and figure from the committed result files."""
    records = load(root)
    tables.write_all(records, root)
    timing = measure(strategy(), corpus()[1], seed=1)
    write_json(timing.as_record(), root / BASELINE / "latency.json")
    write_json(manifest().as_document(), root / "manifest.json")
    write_json(sealed_set(baseline_identity().role).as_document(), root / "final_holdout.json")
    print(f"analysed {len(records)} games into {root}", flush=True)


def main(argv: list[str] | None = None) -> int:
    """Run the requested stage. Returns the process status."""
    arguments = parse_args(argv)
    if arguments.action in ("bench", "all"):
        bench(arguments.out, arguments.sets)
    if arguments.action in ("analyse", "all"):
        analyse(arguments.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
