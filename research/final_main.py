"""`python -m research.final_main` - the one-shot final-holdout evaluation.

A separate entry point on purpose. The everyday research commands live in
`research.candidate_main`, and none of them can reach the sealed set; putting
the final evaluation behind its own module and its own explicit confirmation
means no `all`, no default and no habit can trigger it by accident.

    uv run python -m research.final_main --i-am-consuming-the-final-holdout

Running it a second time is refused, not repeated.
"""

import argparse
from pathlib import Path

from .final_evaluation import run_once
from .validation import FROZEN_C4_SHA256

COMMITMENT = "99bd72e102d8a31e0b0937813166d87afd13034f5e191d834002df9e13358f47"
"""The commitment sealed at Stage 9B-0F and recorded in the 9B-1B freeze."""

CONFIRM = "--i-am-consuming-the-final-holdout"
"""Required, and named for what it costs: after this the set is spent."""


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Read the command line. Reaches no file and plays no game."""
    parser = argparse.ArgumentParser(prog="python -m research.final_main")
    parser.add_argument(CONFIRM, action="store_true", dest="confirmed")
    parser.add_argument("--out", type=Path, default=Path("results"))
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Run the single official evaluation. Returns the process status."""
    arguments = parse_args(argv)
    if not arguments.confirmed:
        raise SystemExit(f"refusing: pass {CONFIRM} to consume the sealed set")
    found = run_once(arguments.out, COMMITMENT, FROZEN_C4_SHA256)
    print(f"final holdout recorded at {found['path']}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
