"""`python -m mars777_police` - start this agent and play its series.

The outermost file in the project. It reads the operator's settings and launch
document, composes the agent, and hands the process to `AutonomousBoot`, which
owns the lifecycle from there: serve, reach the opponent, exchange Step-0, run
the one production `SeriesDriver`, stop. Nothing here plays anything.

**It still does not dial by itself, and it still owns no game.** Joining the
opponent is a bounded startup step inside the coordinator, because two teams
start their agents independently and the first one up finds nothing to reach.
No Step-0, no action and no config leaves this module.

**Exit status is a classification, not a summary.** A local operator refusal
(settings, launch document) is 2, an opponent that never became reachable is 4,
and a peer that refused us for a protocol reason is 5 with its own frozen error
id printed - the identity, never the payload. A genuine local defect is
deliberately *not* translated: it keeps its traceback, because pretending a bug
is an unreachable peer is how a defect survives to the next stage.

Nothing printed here carries key material: the launch document holds no secret,
settings render theirs as `<withheld>`, and the summary names only a directory
and a count.
"""

import argparse
import asyncio
import os
import sys
from pathlib import Path

from . import GROUP_CODE
from .agent_runtime import AgentRuntime
from .app.protocol_errors import LocalDefectError, PeerProtocolError
from .app.sealed_record_values import ActorRole
from .autonomous_boot import AutonomousBoot
from .composition import compose_agent
from .infra.settings import SettingsError, load_runtime_settings
from .launch_input import LaunchInputError, read_launch_document
from .transport.wire_errors import TransportFailureError

ROLE = ActorRole.POLICE
"""The role this repository is; settings are checked against it, never asked."""

SERIES_FILES = 14
"""What one complete series leaves behind, reported rather than recounted."""


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Read the command line. This touches nothing and starts nothing."""
    parser = argparse.ArgumentParser(prog=f"python -m {__package__}")
    parser.add_argument("--launch", required=True, type=Path, help="series launch document")
    return parser.parse_args(argv)


async def play(launch: Path) -> Path:
    """Compose the agent and let the boot coordinator run its whole life."""
    settings = load_runtime_settings(os.environ, expected_role=ROLE)
    document = read_launch_document(launch)
    composition = compose_agent(settings, document.identity, GROUP_CODE)
    runtime = AgentRuntime(composition, settings.local.host, settings.local.port)
    await AutonomousBoot(runtime, settings, document.config, ROLE).run()
    return settings.artifact_root


def main(argv: list[str] | None = None) -> int:
    """Run the agent; return the process status."""
    arguments = parse_args(argv)
    try:
        root = asyncio.run(play(arguments.launch))
    except (SettingsError, LaunchInputError) as failure:
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
