"""`python -m mars777_police.kit_gateway_main` - the group's public front door.

One command brings up everything a partner needs to reach us: the stable group
gateway, its loopback-only admin surface, and one public route in front of them.
The role backends stay where they belong - independent processes in their own
repositories, on private local ports this passes through as configuration and
never advertises.

**Nothing here plays a game.** No board, no strategy, no scent, no digest, no
score: the gateway routes, the backends play, and this owns the operator's view
of the lifecycle. Which side plays which sub-game is the schedule's decision,
not this process's.

**Discovery every run.** The public endpoint is whatever this run's provider
discovery returned. No hostname is remembered between runs, none is committed,
and none is read from a previous session - a stale one is a route to somebody
else's tunnel.

Exit status is a classification: 2 for an operator input the launcher cannot
act on, 4 for a public route that never came up, 0 for a clean shutdown.

The assembly this file used to perform lives in `compose_gateway`, reached
through the facade like every other operation.
"""

import argparse
import asyncio
import sys
from pathlib import Path

from .sdk import (
    AgentSdk,
    KitPublicLauncher,
    KitRole,
    PublicGatewayRequest,
    PublicIngressError,
    SettingsError,
    SoftwareVersionError,
)

__all__ = ["build", "main", "parse_args", "serve"]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Read the command line. This starts nothing and opens no route."""
    parser = argparse.ArgumentParser(prog=f"python -m {__package__}.kit_gateway_main")
    parser.add_argument("--police-endpoint", required=True, help="private police backend MCP url")
    parser.add_argument("--thief-endpoint", required=True, help="private thief backend MCP url")
    parser.add_argument("--first-role", default="police", choices=[one.value for one in KitRole])
    parser.add_argument("--ngrok", required=True, type=Path, help="the operator's ngrok agent")
    parser.add_argument("--evidence-root", default="runtime/friendly", type=Path)
    return parser.parse_args(argv)


def build(arguments: argparse.Namespace) -> KitPublicLauncher:
    """Turn parsed text into one request and let the facade assemble it."""
    return AgentSdk().compose_public_gateway(
        PublicGatewayRequest(
            police_endpoint=arguments.police_endpoint,
            thief_endpoint=arguments.thief_endpoint,
            ngrok=arguments.ngrok,
            first_role=KitRole(arguments.first_role),
            evidence_root=arguments.evidence_root,
        )
    )


async def serve(launcher: KitPublicLauncher) -> None:
    """Open the route, show the operator what is safe to show, and hold it."""
    await launcher.open()
    try:
        for line in launcher.status().operator_lines():
            print(line)
        print("\nready for a partner. Ctrl-C to stop.")
        await asyncio.Event().wait()
    finally:
        await launcher.close()


def main(argv: list[str] | None = None) -> int:
    """Bring the public front door up, and put it away whatever happens."""
    arguments = parse_args(argv)
    try:
        launcher = build(arguments)
    except (SettingsError, SoftwareVersionError) as failure:
        print(f"cannot start: {failure}", file=sys.stderr)
        return 2
    try:
        asyncio.run(serve(launcher))
    except PublicIngressError as failure:
        print(f"cannot start: the public route never came up ({failure})", file=sys.stderr)
        return 4
    except KeyboardInterrupt:
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
