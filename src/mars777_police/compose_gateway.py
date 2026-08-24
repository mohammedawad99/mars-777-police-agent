"""Assembling the group's public front door: gateway, admin surface, one route.

Lifted out of the command line unchanged. The role backends stay independent
processes in their own repositories on private local ports; this only passes
those ports through as configuration and never advertises them.

**Nothing here plays a game.** No board, no strategy, no scent, no digest, no
score: the gateway routes and the backends play. This reads the operator's own
settings for one reason only - the provisioned key identity - and never for a
role decision, which belongs to the schedule.
"""

import os
from collections.abc import Callable
from pathlib import Path

from . import GROUP_CODE
from .app.counted_mode import counted as counted_run
from .app.counted_mode import rehearsal as rehearsal_run
from .app.gatekeeper import Gatekeeper
from .app.kit_handoff import SeriesHandoff
from .app.kit_messages import KitRole
from .app.protocol_errors import LocalDefectError
from .app.public_endpoint_policy import SystemHostResolver
from .app.public_network_workflow import PublicNetworkService
from .app.series_declaration import SeriesDeclarationWriter
from .app.step0_runtime import Step0Runtime
from .artifact_documents import declaration_document
from .compose_series_writer import series_writer
from .composition import compose_agent
from .composition_inputs import keyed_authenticator
from .first_role_source import series_first_role
from .identity import ROLE
from .infra.artifacts import JsonArtifactStore
from .infra.ngrok_ingress import NgrokPublicIngress, fetch
from .infra.ngrok_process import NgrokProcess
from .infra.ngrok_settings import NgrokSettings
from .infra.rate_limit_file import load_rate_limits
from .infra.settings import RuntimeSettings, load_runtime_settings
from .kit_public_launcher import KitPublicLauncher
from .launch_input import read_launch_document
from .operator_requests import PublicGatewayRequest
from .protocol.declaration import Step0Authenticator, locate
from .transport.codec_declaration import decode_step0
from .transport.kit_backend_routes import KitBackendRoutes
from .transport.kit_gateway import KitGroupGateway
from .transport.negotiate_arguments import Step0Handler
from .transport.step0_outbound import send_step0
from .transport.wire_declaration import Step0ExchangeWire

ROUTE_DEADLINE = 1800.0
"""How long one forwarded call may take, bounded well above a turn budget."""

DISCOVER_TUNNELS = "ngrok.discover_tunnels"
"""The one provider operation this repository makes today."""


def gated_fetcher(gate: Gatekeeper) -> Callable[[str], bytes]:
    """Read the provider's Agent API through the gate, and nowhere else.

    The adapter keeps its own seam - it was always given its fetcher - so
    centralising provider-call control changes no tunnel semantics: the same
    request, the same timeout, the same `OSError` on a transport problem, now
    counted and bounded in one place.
    """

    def read(url: str) -> bytes:
        return gate.call(DISCOVER_TUNNELS, lambda: fetch(url))

    return read


def compose_public_gateway(request: PublicGatewayRequest) -> KitPublicLauncher:
    """Assemble the launcher. Nothing is served and no route is opened yet."""
    settings = load_runtime_settings(dict(os.environ), expected_role=ROLE)
    keyed = keyed_authenticator(settings)
    endpoints = {
        KitRole.POLICE: request.police_endpoint,
        KitRole.THIEF: request.thief_endpoint,
    }
    routes = KitBackendRoutes(endpoints, ROUTE_DEADLINE)
    gateway = KitGroupGateway(
        handoff=SeriesHandoff(series_first_role(GROUP_CODE, request.first_role)),
        routes=routes.forwarders(),
        deadline=ROUTE_DEADLINE,
        counted=counted_run() if request.counted else rehearsal_run(),
        write=series_writer(settings, request),
    )
    gate = Gatekeeper(load_rate_limits())
    network = PublicNetworkService(
        ingress=NgrokPublicIngress(
            NgrokProcess(NgrokSettings(executable=request.ngrok)), fetcher=gated_fetcher(gate)
        ),
        resolver=SystemHostResolver(),
        step0=Step0Runtime(GROUP_CODE, Step0Authenticator(keyed)),
    )
    return KitPublicLauncher(
        network=network,
        gateway=gateway,
        group_id=GROUP_CODE,
        backend_endpoints=tuple(endpoints.values()),
        evidence_root=str(request.evidence_root),
        routes=routes,
        step0=(
            None if request.launch is None else _step0_receiver(settings, request.launch, gateway)
        ),
        declared_endpoint=None if request.launch is None else _declared_endpoint(request.launch),
        counted=counted_run() if request.counted else rehearsal_run(),
    )


def _declared_endpoint(launch: Path) -> str:
    """The endpoint our own declaration promises, from the subtree we authored.

    Read through `locate` rather than a slot name: which slot holds us is an
    ordering fact about the pairing, and hard-coding one here would read the
    opponent's endpoint in any pairing that seats us second.
    """
    declaration = read_launch_document(launch).identity.declaration
    _, ours = locate(declaration, GROUP_CODE)
    return ours.mcp_endpoint


def _step0_receiver(
    settings: RuntimeSettings, launch: Path, gateway: KitGroupGateway
) -> Step0Handler:
    """The counted Step-0 receiver, verified against **our own** declaration.

    Composed here rather than routed to a backend because Step-0 is a
    once-per-series, group-level fact: the backends own the six sub-games, and a
    declaration that arrived at one of them would bind an identity the other
    never saw. `PregameSessionRuntime.accept_step0` is the same receiver the
    internal wire uses - nothing about verification is re-implemented for the
    public route, only reached from it.
    """
    document = read_launch_document(launch)
    composition = compose_agent(settings, document.identity, GROUP_CODE)
    ours = document.identity.declaration
    if settings.opponent is None:
        raise LocalDefectError(
            "a Step-0 receiver needs the opponent endpoint to send our own half back;"
            " Step-0 is a mutual exchange and a one-sided one leaves the peer waiting",
        )
    opponent = settings.opponent.url
    declared = SeriesDeclarationWriter(
        JsonArtifactStore(settings.artifact_root), declaration_document
    )

    async def receive(payload: dict[str, object]) -> None:
        wire = Step0ExchangeWire.model_validate(payload)
        composition.pregame.accept_step0(decode_step0(wire))
        declared.write(composition.pregame.declaration)
        gateway.declaration = composition.pregame.declaration
        await send_step0(opponent, composition.pregame.step0.outbound(ours))

    return receive
