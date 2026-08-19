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

from . import GROUP_CODE
from .app.kit_handoff import SeriesHandoff
from .app.kit_messages import KitRole
from .app.public_endpoint_policy import SystemHostResolver
from .app.public_network_workflow import PublicNetworkService
from .app.step0_runtime import Step0Runtime
from .composition_inputs import keyed_authenticator
from .identity import ROLE
from .infra.ngrok_ingress import NgrokPublicIngress
from .infra.ngrok_process import NgrokProcess
from .infra.ngrok_settings import NgrokSettings
from .infra.settings import load_runtime_settings
from .kit_public_launcher import KitPublicLauncher
from .operator_requests import PublicGatewayRequest
from .protocol.declaration import Step0Authenticator
from .transport.kit_backend_routes import KitBackendRoutes
from .transport.kit_gateway import KitGroupGateway

ROUTE_DEADLINE = 1800.0
"""How long one forwarded call may take, bounded well above a turn budget."""


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
        handoff=SeriesHandoff(request.first_role),
        routes=routes.forwarders(),
        deadline=ROUTE_DEADLINE,
    )
    network = PublicNetworkService(
        ingress=NgrokPublicIngress(NgrokProcess(NgrokSettings(executable=request.ngrok))),
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
    )
