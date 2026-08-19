"""`python -m mars777_police` - start this agent and play its series.

The outermost file in the project, and deliberately the thinnest. It reads the
command line, turns it into one semantic request, hands that to the public
facade, and translates whatever comes back into a process status. It composes
nothing, plays nothing and owns no game.

**One compatibility option, not eight.** `--external-mode` is the whole external
selection: it resolves a frozen profile set, the tool surface this process
registers, and the arguments its client sends. It defaults to the internal wire,
so nothing changes for a series that does not ask for the change, and it is
never inferred from a message - a wire cannot be negotiated by the messages
whose encoding it governs. No secret is passed on the command line.

**Exit status is a classification, not a summary.** A local refusal (settings,
launch document, an installation that is not this software) is 2, an opponent
that never became reachable is 4, and a peer that refused us for a protocol
reason is 5 with its own frozen error id printed - the identity, never the
payload. A genuine local defect is deliberately *not* translated: it keeps its
traceback, because pretending a bug is an unreachable peer is how a defect
survives to the next stage.

Nothing printed here carries key material: the launch document holds no secret,
settings render theirs as `<withheld>`, and the summary names only a directory
and a count.
"""

import argparse
import asyncio
import sys
from pathlib import Path

from .sdk import (
    ROLE,
    AgentSdk,
    ExternalMode,
    LaunchInputError,
    LocalDefectError,
    PeerProtocolError,
    SettingsError,
    SoftwareVersionError,
    StrictSeriesRequest,
    TransportFailureError,
)

__all__ = ["ROLE", "SERIES_FILES", "main", "parse_args"]

SERIES_FILES = 14
"""What one complete series leaves behind, reported rather than recounted."""


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Read the command line. This touches nothing and starts nothing."""
    parser = argparse.ArgumentParser(prog=f"python -m {__package__}")
    parser.add_argument("--launch", required=True, type=Path, help="series launch document")
    parser.add_argument(
        "--external-mode",
        type=ExternalMode,
        choices=tuple(ExternalMode),
        default=ExternalMode.STRICT_INTERNAL,
        help="which wire to speak; the external choice is made here, never negotiated",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Run the agent; return the process status."""
    arguments = parse_args(argv)
    request = StrictSeriesRequest(launch=arguments.launch, external_mode=arguments.external_mode)
    try:
        root = asyncio.run(AgentSdk().run_strict_series(request))
    except (SettingsError, LaunchInputError, SoftwareVersionError) as failure:
        print(f"cannot start: {failure}", file=sys.stderr)
        return 2
    except TransportFailureError:
        print("cannot start: the opponent endpoint never became reachable", file=sys.stderr)
        return 4
    except LocalDefectError:
        raise
    except PeerProtocolError as failure:
        print(f"the series stopped: {failure.error_id}", file=sys.stderr)
        return 5
    except KeyboardInterrupt:
        return 0
    print(f"series complete: {SERIES_FILES} artifacts in {root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
