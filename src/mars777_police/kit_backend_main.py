"""`python -m mars777_police.kit_backend_main` - this repository's role backend.

One process, one role, one private local endpoint. It serves the KIT surface the
group gateway forwards to, dials the opponent directly, plays only the sub-games
the frozen schedule gives this role, and writes its own contribution when the
series is done.

**It never learns the other side.** This repository is the Police
implementation; a sub-game the schedule gives the Thief is refused rather than
played, and no strategy, package or state of the sibling is reachable from here.

**Development only.** The run class is `KIT_FRIENDLY_ONLY`, chosen before boot,
so the inbound path delivers to the friendly session and the counted runtime is
never reached - not merely gated.

The launch document is the same one the counted entrypoint reads: it already
carries the negotiated config and, since Stage 8A-1T, the optional flat KIT
terms an external pairing agreed.

Like the counted entrypoint, this file parses, asks the facade, and classifies.
The assembly it used to perform lives in `compose_backend`, one layer down.
"""

import argparse
import asyncio
import sys
from pathlib import Path

from .sdk import (
    AgentSdk,
    KitBackendBoot,
    KitRole,
    KitRoleBackend,
    LaunchInputError,
    RoleBackendRequest,
    SettingsError,
    SoftwareVersionError,
)

__all__ = ["build", "main", "parse_args", "persist"]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Read the command line. This binds nothing and dials nobody."""
    parser = argparse.ArgumentParser(prog=f"python -m {__package__}.kit_backend_main")
    parser.add_argument("--launch", required=True, type=Path, help="series launch document")
    parser.add_argument("--port", required=True, type=int, help="private local port to serve")
    parser.add_argument("--opponent", required=True, help="the opponent's public MCP url")
    parser.add_argument("--gateway-admin", required=True, help="the gateway's loopback admin url")
    parser.add_argument(
        "--first-role",
        default=None,
        choices=[one.value for one in KitRole],
        help="sub-game-1 role, for a pairing the shared contract does not name",
    )
    parser.add_argument("--evidence-root", default="runtime/friendly", type=Path)
    return parser.parse_args(argv)


def build(arguments: argparse.Namespace) -> KitBackendBoot:
    """Turn parsed text into one request and let the facade assemble it."""
    return AgentSdk().compose_role_backend(
        RoleBackendRequest(
            launch=arguments.launch,
            port=arguments.port,
            opponent=arguments.opponent,
            gateway_admin=arguments.gateway_admin,
            first_role=arguments.first_role,
            evidence_root=arguments.evidence_root,
        )
    )


def persist(backend: KitRoleBackend, root: Path) -> str:
    """Write this role's contribution to the development evidence root."""
    return AgentSdk().write_contribution(backend, root)


def main(argv: list[str] | None = None) -> int:
    """Serve, play this role's rows, write the contribution, and stop."""
    arguments = parse_args(argv)
    try:
        boot = build(arguments)
    except (SettingsError, LaunchInputError, SoftwareVersionError) as failure:
        print(f"cannot start: {failure}", file=sys.stderr)
        return 2
    try:
        asyncio.run(boot.run())
    except KeyboardInterrupt:
        return 0
    print(f"contribution written to {persist(boot.backend, arguments.evidence_root)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
