"""`python -m mars777_police.kit_gateway_main` - the group's public front door.

One command brings up everything a partner needs to reach us: the stable group
gateway, its loopback-only admin surface, and one public route in front of them.
The role backends stay where they belong - independent processes in their own
repositories, on private local ports this passes through as configuration and
never advertises.

**Nothing here plays a game.** No board, no strategy, no scent, no digest, no
score: the gateway routes, the backends play, and this owns the lifecycle and
the operator's view of it. It reads this repository's own operator settings for
one reason only - the provisioned key identity - and never for a role decision:
which side plays which sub-game is the schedule's, not this process's.

**Discovery every run.** The public endpoint is whatever this run's provider
discovery returned. No hostname is remembered between runs, none is committed,
and none is read from a previous session - a stale one is a route to somebody
else's tunnel.

Exit status is a classification: 2 for an operator input the launcher cannot
act on, 4 for a public route that never came up, 0 for a clean shutdown.
"""

import argparse
import asyncio
import os
import sys
from pathlib import Path

from . import GROUP_CODE
from .__main__ import ROLE
from .app.kit_handoff import SeriesHandoff
from .app.kit_messages import KitRole
from .app.public_endpoint_policy import SystemHostResolver
from .app.public_ingress import PublicIngressError
from .app.public_network_workflow import PublicNetworkService
from .app.step0_runtime import Step0Runtime
from .composition_inputs import keyed_authenticator
from .infra.ngrok_ingress import NgrokPublicIngress
from .infra.ngrok_process import NgrokProcess
from .infra.ngrok_settings import NgrokSettings
from .infra.settings import SettingsError, load_runtime_settings
from .kit_public_launcher import KitPublicLauncher
from .protocol.declaration import Step0Authenticator
from .transport.kit_backend_routes import KitBackendRoutes
from .transport.kit_gateway import KitGroupGateway

ROUTE_DEADLINE = 1800.0
"""How long one forwarded call may take, bounded well above a turn budget."""


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
    """Assemble the launcher. Nothing is served and no route is opened yet."""
    settings = load_runtime_settings(dict(os.environ), expected_role=ROLE)
    keyed = keyed_authenticator(settings)
    endpoints = {
        KitRole.POLICE: arguments.police_endpoint,
        KitRole.THIEF: arguments.thief_endpoint,
    }
    routes = KitBackendRoutes(endpoints, ROUTE_DEADLINE)
    gateway = KitGroupGateway(
        handoff=SeriesHandoff(KitRole(arguments.first_role)),
        routes=routes.forwarders(),
        deadline=ROUTE_DEADLINE,
    )
    network = PublicNetworkService(
        ingress=NgrokPublicIngress(NgrokProcess(NgrokSettings(executable=arguments.ngrok))),
        resolver=SystemHostResolver(),
        step0=Step0Runtime(GROUP_CODE, Step0Authenticator(keyed)),
    )
    return KitPublicLauncher(
        network=network,
        gateway=gateway,
        group_id=GROUP_CODE,
        backend_endpoints=tuple(endpoints.values()),
        evidence_root=str(arguments.evidence_root),
        routes=routes,
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
    except SettingsError as failure:
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
