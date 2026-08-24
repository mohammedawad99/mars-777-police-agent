"""Putting the group gateway behind one public route, and taking it down again.

Two things already existed and neither had a production caller: the group
gateway, and the provider-neutral `PublicIngressPort`. This is the seam between
them, and it is deliberately thin. What a public endpoint *is* stays with the
existing policy - HTTPS, no userinfo, no query or fragment, the exact FastMCP
path, a globally routable host - and this only owns the order the two happen in
and the guarantee that both are released whichever way the run ends.

**One endpoint is advertised, and it is the group's.** `teams.<group>.mcp_endpoint`
is group-level; the role backends stay on private local ports that never leave
this process - not in the operator banner, not in a pairing document, not in an
artifact.

**Nothing is remembered between runs.** The endpoint is whatever this run's
discovery returned, and closing forgets it: a stale hostname reused after a
restart is a route to somebody else's tunnel.

**A declaration that names a different endpoint never reaches a peer.** When
this route carries Step-0, the declaration we are about to authenticate has
already been written, and `mcp_endpoint` is inside the authenticated core. If
it does not name the ingress discovery actually returned, those bytes claim an
address no opponent can reach - the mismatch `FR-015b` exists to prevent. The
opponent found exactly this in a rehearsal, where the launch document carried a
placeholder and the transport happened to work because the peer URL was
configured separately. Discovery and the declaration are compared here, once,
before anything is served to anyone.
"""

from dataclasses import dataclass, field

from .app.counted_mode import CountedRun, rehearsal
from .app.protocol_errors import LocalDefectError
from .app.public_endpoint_values import LocalPeerEndpoint, OwnPublicPeerEndpoint
from .app.public_network_workflow import PublicNetworkService
from .app.run_class import RunClass
from .ingress_release import release
from .public_launch_values import PublicLaunchStatus
from .transport.kit_backend_routes import KitBackendRoutes
from .transport.kit_gateway import KitGroupGateway
from .transport.kit_gateway_server import build_gateway_admin, build_gateway_tools
from .transport.kit_serving import ServedHttp, serve_http
from .transport.negotiate_arguments import Step0Handler

LOOPBACK = "127.0.0.1"
"""The admin surface is loopback-only; it is never part of the public route."""


@dataclass(slots=True)
class KitPublicLauncher:
    """One group ingress, one gateway, two private backends, one teardown."""

    network: PublicNetworkService
    gateway: KitGroupGateway
    group_id: str
    backend_endpoints: tuple[str, ...]
    evidence_root: str
    host: str = field(default=LOOPBACK)
    admin_port: int = field(default=0)
    public_port: int = field(default=0)
    step0: "Step0Handler | None" = field(default=None)
    """Where an authenticated Step-0 goes, or `None` for a route that carries none.

    Once per series and group-level, so it is received here rather than routed to
    a backend: the six sub-games are what the backends own."""

    counted: CountedRun = field(default_factory=rehearsal)
    """What this run is allowed to be worth. A rehearsal unless someone said otherwise."""

    declared_endpoint: str | None = field(default=None)
    """What our own Step-0 declaration says a peer should reach us at, if any."""

    endpoint: OwnPublicPeerEndpoint | None = field(default=None)
    routes: KitBackendRoutes | None = field(default=None)
    _served: list[ServedHttp] = field(default_factory=list)

    @property
    def is_live(self) -> bool:
        """Whether this launcher currently holds a public route."""
        return self.endpoint is not None

    async def open(self) -> OwnPublicPeerEndpoint:
        """Serve both surfaces, then expose the public one. Release on any failure."""
        try:
            tools = build_gateway_tools(self.gateway, step0=self.step0)
            self.public_port = await self._serve(tools, 0)
            self.admin_port = await self._serve(build_gateway_admin(self.gateway), self.admin_port)
            self.endpoint = self.network.establish(LocalPeerEndpoint(self.host, self.public_port))
            self._require_declared(self.endpoint)
        except BaseException:
            await self.close()
            raise
        return self.endpoint

    def _require_declared(self, discovered: OwnPublicPeerEndpoint) -> None:
        """Refuse a route whose declaration names somewhere else.

        Only when a declaration exists: a route carrying no Step-0 has promised
        a peer nothing, and there is no claim to contradict.
        """
        if self.declared_endpoint is None or self.declared_endpoint == discovered.url:
            return
        raise LocalDefectError(
            f"our declaration names {self.declared_endpoint!r} but this run's ingress is"
            f" {discovered.url!r}; authenticating that declaration would hand the opponent"
            " an address it cannot reach",
        )

    async def close(self) -> None:
        """Tear the route down, then both servers. Safe from any point, and twice."""
        served, self._served, self.endpoint = self._served, [], None
        routes, self.routes = self.routes, None
        try:
            if routes is not None:
                await routes.close()
        finally:
            try:
                self.network.ingress.close()
            finally:
                for one in reversed(served):
                    await release(one.task, one.listener)

    def status(self) -> PublicLaunchStatus:
        """The safe operator view: no secret, no private endpoint, no internals."""
        return PublicLaunchStatus(
            group_id=self.group_id,
            public_endpoint=None if self.endpoint is None else self.endpoint.url,
            run_class=(
                RunClass.COUNTED_CAPABLE if self.counted.is_counted else RunClass.KIT_FRIENDLY_ONLY
            ),
            evidence_root=self.evidence_root,
            backends_configured=len(self.backend_endpoints),
        )

    async def _serve(self, server: object, port: int) -> int:
        """Serve one surface through the transport owner, and keep it for release."""
        served = await serve_http(server, self.host, port)  # type: ignore[arg-type]
        self._served.append(served)
        return served.port
