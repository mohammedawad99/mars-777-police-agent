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
"""

import argparse
import asyncio
import os
import sys
from pathlib import Path

from . import GROUP_CODE
from .__main__ import ROLE
from .app.commitment_codecs import CommitmentCodec
from .app.competitive_strategy import CompetitiveStrategy
from .app.friendly_backend_evidence import backend_rows
from .app.friendly_evidence import DevelopmentEvidenceStore
from .app.friendly_merge import contribution_document, friendly_contribution_name
from .app.kit_friendly import KitFriendlySession
from .app.kit_messages import KitRole
from .app.kit_payload import PeerPayload
from .app.kit_session import KitSessionContext
from .app.protocol_errors import LocalDefectError
from .app.run_class import RunClassification
from .domain.scent_model_default import default_scent_model
from .infra.artifacts import JsonArtifactStore
from .infra.clock import SystemClock
from .infra.settings import SettingsError, load_runtime_settings
from .kit_backend import KitRoleBackend
from .kit_backend_boot import KitBackendBoot, backend_client
from .launch_input import LaunchInputError, read_launch_document
from .protocol.secure_nonce import SecretsNonceSource
from .transport.peer_transport import FastMcpPeerTransport

BACKEND_DEADLINE = 1800.0
"""How long this role waits to be handed a sub-game, bounded well above a turn."""


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Read the command line. This binds nothing and dials nobody."""
    parser = argparse.ArgumentParser(prog=f"python -m {__package__}.kit_backend_main")
    parser.add_argument("--launch", required=True, type=Path, help="series launch document")
    parser.add_argument("--port", required=True, type=int, help="private local port to serve")
    parser.add_argument("--opponent", required=True, help="the opponent's public MCP url")
    parser.add_argument("--gateway-admin", required=True, help="the gateway's loopback admin url")
    parser.add_argument("--first-role", default="police", choices=[one.value for one in KitRole])
    parser.add_argument("--evidence-root", default="runtime/friendly", type=Path)
    return parser.parse_args(argv)


def build(arguments: argparse.Namespace) -> KitBackendBoot:
    """Assemble this role's backend. Nothing is served and nothing is dialled."""
    load_runtime_settings(dict(os.environ), expected_role=ROLE)
    document = read_launch_document(arguments.launch)
    if document.kit_terms is None:
        raise LaunchInputError("a KIT friendly needs the agreed flat terms in the launch document")
    friendly = KitFriendlySession(RunClassification.friendly(kit_terms_agreement=True))
    context = KitSessionContext(
        GROUP_CODE,
        KitRole(ROLE.value),
        PeerPayload(document.kit_terms),
        1,
        friendly=friendly,
    )
    client = backend_client(arguments.opponent, BACKEND_DEADLINE)
    backend = KitRoleBackend(
        context=context,
        friendly=friendly,
        transport=FastMcpPeerTransport(client),
        settled=_unwired,
        config=document.config,
        role=ROLE,
        strategy=CompetitiveStrategy(),
        model=default_scent_model(),
        nonces=SecretsNonceSource(),
        clock=SystemClock(),
        codec=CommitmentCodec.KIT_CORE_COMMITMENT_V1,
        deadline=BACKEND_DEADLINE,
        first_role=KitRole(arguments.first_role),
    )
    return KitBackendBoot(backend, context, client, arguments.gateway_admin, arguments.port)


async def _unwired(sub_game: int) -> None:  # pragma: no cover - replaced before play
    raise LocalDefectError("this backend was never given a gateway to report settlement to")


def persist(backend: KitRoleBackend, root: Path) -> str:
    """Write this role's contribution to the development evidence root."""
    pairing = backend.friendly.pairing
    if pairing is None:
        raise LocalDefectError("a contribution needs the pairing a greeting established")
    document = contribution_document(
        role=backend.kit_role,
        game_id=pairing.game_id,
        game_uid=pairing.game_uid,
        our_group=pairing.our_group,
        peer_group=pairing.peer_group,
        rows=backend_rows(
            role=backend.kit_role,
            outcomes=backend.outcomes,
            chains=backend.chains,
            verified=backend.verified,
            witnessed=backend.witnessed,
        ),
    )
    store = DevelopmentEvidenceStore(JsonArtifactStore(root))
    stored = store.store(friendly_contribution_name(pairing.game_id, backend.kit_role), document)
    return stored.path


def main(argv: list[str] | None = None) -> int:
    """Serve, play this role's rows, write the contribution, and stop."""
    arguments = parse_args(argv)
    try:
        boot = build(arguments)
    except (SettingsError, LaunchInputError) as failure:
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
