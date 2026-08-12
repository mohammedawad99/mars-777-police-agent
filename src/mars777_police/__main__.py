"""`python -m mars777_police` - start this agent and wait to be stopped.

The outermost file in the project. It reads the operator's settings and launch
document, composes the agent, raises its ingress, and then does nothing but wait -
because R6 owns being alive, not playing. No Step-0 leaves this module and no
turn is taken; an orchestrator drives the runner once the process is up.

**It serves; it does not dial.** `PeerClient.__aenter__` opens a real connection,
so joining the opponent cannot succeed until they are listening - and two teams
start their agents independently. Making that part of startup would turn boot
into a race neither side controls, so the outbound session is the orchestrator's
to open, through `AgentRuntime.connect`, when there is someone to talk to.

**Waiting is the server, not a loop.** The process parks on the served ingress,
so it costs nothing while idle. The server already installs portable interrupt
handling on both Linux and Windows, so a Ctrl-C makes it return normally and we
simply notice - adding a second handler would only take that graceful path away.
`KeyboardInterrupt` remains the fallback, and `main` returns 0 for it.

Failures before the agent exists exit non-zero without starting anything, and
nothing printed here carries key material: the launch document holds no secret,
and settings deliberately render theirs as `<withheld>`.
"""

import argparse
import asyncio
import os
import sys
from pathlib import Path

from . import GROUP_CODE
from .agent_runtime import AgentRuntime
from .app.sealed_record_values import ActorRole
from .composition import compose_agent
from .infra.settings import SettingsError, load_runtime_settings
from .launch_input import LaunchInputError, read_launch_document

ROLE = ActorRole.POLICE
"""The role this repository is; settings are checked against it, never asked."""


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Read the command line. This touches nothing and starts nothing."""
    parser = argparse.ArgumentParser(prog=f"python -m {__package__}")
    parser.add_argument("--launch", required=True, type=Path, help="series launch document")
    return parser.parse_args(argv)


async def serve(launch: Path) -> None:
    """Compose, boot, and wait until interrupted. Sends nothing to the peer."""
    settings = load_runtime_settings(os.environ, expected_role=ROLE)
    identity = read_launch_document(launch)
    composition = compose_agent(settings, identity, GROUP_CODE)
    runtime = AgentRuntime(composition, settings.local.host, settings.local.port)
    await runtime.serve()
    try:
        await runtime.wait_closed()
    finally:
        await runtime.stop()


def main(argv: list[str] | None = None) -> int:
    """Run the agent; return the process status."""
    arguments = parse_args(argv)
    try:
        asyncio.run(serve(arguments.launch))
    except (SettingsError, LaunchInputError) as failure:
        print(f"cannot start: {failure}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
