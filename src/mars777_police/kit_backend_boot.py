"""Bringing one role backend up, playing its rows, and putting it away.

Three resources in a fixed order, and every failure path releases whichever of
them exists: the private inbound surface the gateway forwards to, the held
outbound session to the opponent, and the loopback report that tells the gateway
this sub-game owes nothing more.

**The private surface is private.** It binds loopback by default and its address
is configuration the operator already knows - it is never discovered, never
advertised and never written into a document a peer will read.

Nothing here decides a rule: the schedule says which sub-games are ours, the
backend plays them, and this owns only the lifecycle around that.
"""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any, cast

from .app.kit_session import KitSessionContext
from .app.peer_supervision import PeerDeadline, TimeoutPolicy
from .app.protocol_errors import LocalDefectError
from .domain.terminal import Outcome
from .ingress_release import release
from .kit_backend import KitRoleBackend
from .transport.client import PeerClient
from .transport.handlers import PeerOperations
from .transport.kit_admin_client import KitAdminClient
from .transport.kit_serving import ServedHttp, serve_http
from .transport.server import build_server
from .transport.transport_profiles import TransportEnvelopeProfile

LOOPBACK = "127.0.0.1"


def backend_client(opponent: str, deadline: float) -> PeerClient:
    """The outbound half: one held KIT session to the opponent's public route."""
    return PeerClient(
        opponent,
        PeerDeadline(TimeoutPolicy(deadline)),
        TransportEnvelopeProfile.KIT_EXTERNAL,
    )


@dataclass(slots=True)
class KitBackendBoot:
    """One role backend's whole life: serve, dial, play, report, release."""

    backend: KitRoleBackend
    context: KitSessionContext
    client: PeerClient
    admin_url: str
    port: int
    host: str = field(default=LOOPBACK)
    served: ServedHttp | None = field(default=None)

    async def run(self) -> dict[int, Outcome]:
        """Serve the private surface, play our rows, and release everything."""
        await self._serve()
        try:
            async with KitAdminClient(self.admin_url) as admin, self.client:
                self._wire(admin)
                return dict(await self.backend.run())
        finally:
            if self.served is not None:
                await release(self.served.task, self.served.listener)

    def _wire(self, admin: KitAdminClient) -> None:
        """Give the backend the five loopback calls it cannot construct itself.

        All four, together: the settlement report the gateway routes on, the two
        that let a two-process group put its six rows back into one series, and
        the one that carries this sub-game's official documents to where the
        group's fourteen files are assembled, and the whole-series digest that
        licenses the result. Wiring one and leaving the others
        at their refusal defaults is what a rehearsal caught - every unit test
        injected its own and passed.
        """
        self.backend.settled = admin.settled
        self.backend.settlement.contribute = admin.contribute
        self.backend.settlement.series_rows = self._series_rows(admin)
        self.backend.artifacts.contribute = admin.contribute_artifact
        self.backend.settlement.report_series = admin.series_settled

    @staticmethod
    def _series_rows(
        admin: KitAdminClient,
    ) -> "Callable[[], Awaitable[tuple[dict[str, Any], ...]]]":
        """The group's assembled series, as the settler expects to receive it."""

        async def read() -> tuple[dict[str, Any], ...]:
            return tuple(await admin.series_rows())

        return read

    async def _serve(self) -> None:
        """Serve the private surface the gateway forwards to, and keep it for release."""
        self.served = await serve_http(
            build_server(
                cast(PeerOperations, _Unreached()),
                name=f"mars777-{self.context.our_role.value}-backend",
                profile=TransportEnvelopeProfile.KIT_EXTERNAL,
                context=self.context,
            ),
            self.host,
            self.port,
        )


class _Unreached:
    """The counted runtime, which a friendly must never reach.

    Not a stub standing in for something: under `KIT_FRIENDLY_ONLY` the inbound
    path delivers to the friendly session and never calls these at all, so any
    call here is a wiring defect and says so rather than quietly working.
    """

    def __getattr__(self, name: str) -> object:
        def refuse(*arguments: object, **keywords: object) -> object:
            raise LocalDefectError(f"a development friendly reached the counted runtime ({name})")

        return refuse
