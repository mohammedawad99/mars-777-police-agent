"""`python -m mars777_police.replay_main` - replay and verify a game log.

The viewer `REPLAY-001` asks for, as a command an operator or a grader can run
against evidence they were handed. It parses, asks the facade, and formats;
every verdict it prints came from an authority that already existed.

**Exit status is a classification, and absence is not an accusation.** `0` means
the replay ran and **every source-required applicable** commitment was present
and matched. `2` means the evidence could not be read or replayed - a local
refusal, printed as a sentence rather than as a traceback. `3` means the replay
ran and **found something**: a digest that did not correspond, or a step the
rules say could not have happened. `4` means the replay ran but the audit is
**incomplete** - some commitment could not be checked because its nonce was
never disclosed. A grader can gate on "not 0" without reading a word, and still
tell an accusation from a gap.
"""

import argparse
import sys
from pathlib import Path

from .sdk import (
    AgentSdk,
    ReplayCheck,
    ReplayError,
    ReplaySession,
    ReplayStep,
    audit_complete,
    board_lines,
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Read the command line. This opens nothing."""
    parser = argparse.ArgumentParser(prog=f"python -m {__package__}.replay_main")
    parser.add_argument("--log", required=True, type=Path, help="an official sub-game log")
    parser.add_argument("--config", required=True, type=Path, help="the config artifact it names")
    parser.add_argument("--root", type=Path, help="an evidence root every path must stay inside")
    parser.add_argument("--summary", action="store_true", help="print the verdict only")
    parser.add_argument("--step", type=int, help="print one step instead of all of them")
    return parser.parse_args(argv)


def show(session: ReplaySession, step_number: int | None) -> None:
    """Print the replay: one step, or every step in order."""
    chosen = session.steps if step_number is None else _one(session, step_number)
    for step in chosen:
        print(f"\n-- step {step.number} --")
        for turn in step.turns:
            print(f"   {turn.role:<6} {turn.action:<28} {turn.check.value}")
            if turn.hint is not None:
                print(f"          hint: {turn.hint}")
        for line in board_lines(step):
            print(f"   {line}")
        print(f"   semantic: {step.semantic}")


def _one(session: ReplaySession, number: int) -> tuple[ReplayStep, ...]:
    for step in session.steps:
        if step.number == number:
            return (step,)
    raise ReplayError(f"this log has no step {number}")


def report(session: ReplaySession) -> int:
    """Print the verdict and return the process status it implies."""
    found = session.summary()
    print(f"game_id        {found.game_id}")
    print(f"sub_game       {found.sub_game}")
    print(f"config_sha256  {found.config_sha256}")
    print(f"evidence       {found.evidence_class}")
    print(f"steps          {found.steps}")
    print(f"commitments    {found.crypto.value}")
    print(f"recorded       {found.recorded_result}")
    print(f"tampered step  {found.tampered_step}")
    print(f"semantic       {found.semantic_verdict}")
    print(f"agrees         {found.outcome_agrees}")
    for note in found.notes:
        print(f"note           {note}")
    print(f"complete       {audit_complete(found)}")
    if found.crypto is ReplayCheck.TAMPERED or found.semantic_verdict != "CONSISTENT":
        return 3
    return 0 if audit_complete(found) else 4


def main(argv: list[str] | None = None) -> int:
    """Replay one sub-game; return the process status."""
    arguments = parse_args(argv)
    try:
        session = AgentSdk().open_replay(arguments.log, arguments.config, arguments.root)
        if not arguments.summary:
            show(session, arguments.step)
        return report(session)
    except ReplayError as failure:
        print(f"cannot replay: {failure}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
