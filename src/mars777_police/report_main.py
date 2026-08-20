"""`python -m mars777_police.report_main` - send this game's report to the lecturer.

Appendix E rule 32 requires the result of every legal game to be reported
automatically through the Gmail interface, and rule 35 makes each group's own
separate report the condition for being credited at all. This is the command
that does it, over the result artifact the series already agreed and wrote.

    uv run python -m mars777_police.report_main --result artifacts/result_<game_id>.json

**A game fact is never rewritten here.** Who won, the scores and the agreed
digest were settled before this command existed; it attaches the result document
byte-for-byte and reports what the provider said about the message. A delivery
failure leaves the result exactly as it was and says `REPORTING_INCOMPLETE`.

**Exit status is a classification.** `0` the provider accepted the report; `2` a
local refusal - no credential, no recipient reachable, an unreadable or
unagreed result - printed as a sentence rather than a traceback; `3` the report
was eligible and correctly built but the provider did **not** accept it, so
reporting is incomplete and must be retried. Nothing prints a token.
"""

import argparse
import sys
from pathlib import Path

from .app.replay_values import ReplayError
from .app.report_values import ReportError
from .compose_report import ReportOutcome, send_game_report
from .infra.gmail_credentials import GmailCredentialError
from .sdk import REPORTS_ADDRESS

INCOMPLETE = "REPORTING_INCOMPLETE"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Read the command line. This opens no file and reaches no provider."""
    parser = argparse.ArgumentParser(prog=f"python -m {__package__}.report_main")
    parser.add_argument("--result", required=True, type=Path, help="the agreed result artifact")
    parser.add_argument("--root", type=Path, help="an evidence root the result must stay inside")
    return parser.parse_args(argv)


def report(outcome: ReportOutcome) -> int:
    """Print what happened, and return the process status it implies."""
    print(f"game_id        {outcome.report.game_id}")
    print(f"group_id       {outcome.report.group_id}")
    print(f"recipient      {REPORTS_ADDRESS}")
    print(f"attachment     {outcome.report.attachment_name}")
    print(f"result_sha256  {outcome.report.result_sha256}")
    print(f"accepted       {outcome.delivery.accepted}")
    print(f"message_id     {outcome.delivery.provider_message_id}")
    print(f"evidence       {outcome.evidence}")
    if outcome.delivery.accepted:
        return 0
    print(f"failure        {outcome.delivery.failure}")
    print(f"status         {INCOMPLETE}", file=sys.stderr)
    return 3


def main(argv: list[str] | None = None) -> int:
    """Send one game report; return the process status."""
    arguments = parse_args(argv)
    try:
        return report(send_game_report(arguments.result, arguments.root))
    except GmailCredentialError as missing:
        print(f"cannot report: {missing}", file=sys.stderr)
        return 2
    except (ReportError, ReplayError) as refusal:
        print(f"cannot report: {refusal}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
