"""A recording ingress and a launcher built from it. No provider is involved."""

from dataclasses import dataclass, field

from test_readiness_gate import OWN

from mars777_police.app.kit_handoff import SeriesHandoff
from mars777_police.app.kit_messages import KitRole
from mars777_police.app.public_endpoint_policy import HostResolver
from mars777_police.app.public_endpoint_values import LocalPeerEndpoint, OwnPublicPeerEndpoint
from mars777_police.app.public_network_workflow import PublicNetworkService
from mars777_police.kit_public_launcher import KitPublicLauncher
from mars777_police.transport.kit_gateway import KitGroupGateway

POLICE_BACKEND = "http://127.0.0.1:18931/mcp"
THIEF_BACKEND = "http://127.0.0.1:18932/mcp"


@dataclass(slots=True)
class TrackingIngress:
    """A `PublicIngressPort` that records what it was asked to expose."""

    endpoint: OwnPublicPeerEndpoint
    opened: LocalPeerEndpoint | None = field(default=None)
    closed: bool = field(default=False)
    live: bool = field(default=False)

    def open(self, local: LocalPeerEndpoint) -> OwnPublicPeerEndpoint:
        self.opened, self.live = local, True
        return self.endpoint

    def current(self) -> OwnPublicPeerEndpoint | None:
        return self.endpoint if self.live else None

    def is_live(self) -> bool:
        return self.live

    def close(self) -> None:
        self.closed, self.live = True, False


class _Resolver:
    """The production resolver's shape: a routable answer, or a loopback one."""

    def resolve(self, host: str) -> tuple[str, ...]:
        local = host in ("localhost", "127.0.0.1", "::1") or host.endswith(".local")
        return ("127.0.0.1",) if local else ("93.184.216.34",)


def tracking_ingress(url: str = "") -> TrackingIngress:
    return TrackingIngress(OwnPublicPeerEndpoint(url) if url else OWN)


def service(ingress: TrackingIngress) -> PublicNetworkService:
    from composed_builders import KEY_ID, SHARED

    from mars777_police.app.auth_values import AuthProfile
    from mars777_police.app.step0_runtime import Step0Runtime
    from mars777_police.protocol.declaration import Step0Authenticator
    from mars777_police.protocol.keyed_auth import HmacSha256Provider, KeyedAuthenticator

    keyed = KeyedAuthenticator(
        AuthProfile.HMAC_SHA256, KEY_ID, HmacSha256Provider({KEY_ID.value: SHARED})
    )
    resolver: HostResolver = _Resolver()  # type: ignore[assignment]
    return PublicNetworkService(
        ingress=ingress,  # type: ignore[arg-type]
        resolver=resolver,
        step0=Step0Runtime("MaRs-777", Step0Authenticator(keyed)),
    )


def launcher(network: PublicNetworkService, admin_port: int = 0) -> KitPublicLauncher:
    gateway = KitGroupGateway(
        handoff=SeriesHandoff(KitRole.POLICE),
        routes={},
        deadline=30.0,
    )
    return KitPublicLauncher(
        network=network,
        gateway=gateway,
        group_id="MaRs-777",
        backend_endpoints=(POLICE_BACKEND, THIEF_BACKEND),
        evidence_root="runtime/friendly",
        admin_port=admin_port,
    )
