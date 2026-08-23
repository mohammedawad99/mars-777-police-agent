"""Assembling this repository's role backend, and writing what it produced.

Both halves used to live in the command line. Nothing about them changed on the
way here: the same friendly session, the same frozen schedule, the same strategy
production already composes, and the same development-evidence store that
refuses any name a counted artifact could be mistaken for.

**Development only.** The run class is `KIT_FRIENDLY_ONLY`, chosen before boot,
so the inbound path delivers to the friendly session and the counted runtime is
never reached - not merely gated.
"""

import os
from pathlib import Path

from . import GROUP_CODE
from .app.commitment_codecs import CommitmentCodec
from .app.competitive_strategy import CompetitiveStrategy
from .app.friendly_backend_evidence import backend_rows
from .app.friendly_evidence import DevelopmentEvidenceStore
from .app.friendly_merge import contribution_document, friendly_contribution_name
from .app.kit_backend_settlement import BackendSettlement
from .app.kit_friendly import KitFriendlySession
from .app.kit_messages import KitRole
from .app.kit_payload import PeerPayload
from .app.kit_session import KitSessionContext
from .app.protocol_errors import LocalDefectError
from .app.run_class import RunClassification
from .app.scent_registration import registered_model
from .domain.scent_model_default import default_scent_model
from .first_role_source import series_first_role
from .identity import ROLE
from .infra.artifacts import JsonArtifactStore
from .infra.clock import SystemClock
from .infra.settings import load_runtime_settings
from .kit_backend import KitRoleBackend
from .kit_backend_boot import KitBackendBoot, backend_client
from .launch_input import LaunchInputError, read_launch_document
from .operator_requests import RoleBackendRequest
from .protocol.secure_nonce import SecretsNonceSource
from .transport.peer_transport import FastMcpPeerTransport

BACKEND_DEADLINE = 1800.0
"""How long this role waits to be handed a sub-game, bounded well above a turn."""


def compose_role_backend(request: RoleBackendRequest) -> KitBackendBoot:
    """Assemble this role's backend. Nothing is served and nothing is dialled."""
    load_runtime_settings(dict(os.environ), expected_role=ROLE)
    document = read_launch_document(request.launch)
    if document.kit_terms is None:
        raise LaunchInputError("a KIT friendly needs the agreed flat terms in the launch document")
    friendly = KitFriendlySession(RunClassification.friendly(kit_terms_agreement=True))
    context = KitSessionContext(
        GROUP_CODE,
        KitRole(ROLE.value),
        PeerPayload(document.kit_terms),
        1,
        scent=registered_model(default_scent_model()),
        friendly=friendly,
    )
    client = backend_client(request.opponent, BACKEND_DEADLINE)
    backend = KitRoleBackend(
        context=context,
        friendly=friendly,
        transport=FastMcpPeerTransport(client),
        settled=_unwired,
        settlement=BackendSettlement(contribute=_uncontributed, series_rows=_unassembled),
        config=document.config,
        role=ROLE,
        strategy=CompetitiveStrategy(),
        model=default_scent_model(),
        nonces=SecretsNonceSource(),
        clock=SystemClock(),
        codec=CommitmentCodec.KIT_CORE_COMMITMENT_V1,
        deadline=BACKEND_DEADLINE,
        first_role=series_first_role(GROUP_CODE, request.first_role),
    )
    return KitBackendBoot(backend, context, client, request.gateway_admin, request.port)


async def _unwired(sub_game: int) -> None:  # pragma: no cover - replaced before play
    raise LocalDefectError("this backend was never given a gateway to report settlement to")


async def _uncontributed(row: dict[str, object]) -> None:  # pragma: no cover - replaced
    raise LocalDefectError("this backend was never given a group to contribute its rows to")


async def _unassembled() -> tuple[dict[str, object], ...]:  # pragma: no cover - replaced
    raise LocalDefectError("this backend was never given a way to read the group's series")


def write_contribution(backend: KitRoleBackend, root: Path) -> str:
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
        series_consensus_sha256=backend.settlement.agreed,
    )
    store = DevelopmentEvidenceStore(JsonArtifactStore(root))
    stored = store.store(friendly_contribution_name(pairing.game_id, backend.kit_role), document)
    return stored.path
