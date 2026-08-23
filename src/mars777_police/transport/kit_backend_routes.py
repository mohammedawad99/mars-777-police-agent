"""The gateway's outbound half: one held session to each private role backend.

The gateway routes; these are the wires it routes over. One `PeerClient` per
role, opened once and held for the series, because a session re-established per
call is the failure Stage 4E measured over a real tunnel - thirty operations
each opening their own session failed from the twenty-first onward.

**Private, and they stay private.** These endpoints are local implementation
detail: they are never advertised to a peer, never written into a declaration
and never printed in the operator banner. The only address anybody outside this
process learns is the group's one public route.

**A held session that dies is replaced once, and only for a transport failure.**
Holding one session is right - Stage 4E measured thirty operations each opening
their own session failing from the twenty-first onward - but a cache that never
reopens turns one dropped connection into a backend that is unreachable for the
rest of the series. `TransportFailureError` means the wire failed and a fresh
session is the repair; a `ToolError` from the backend is a *decision* and is
re-raised untouched, because retrying a refusal would only hide it. The retry is
exactly one: a second transport failure propagates.
"""

from collections.abc import Awaitable, Callable, Mapping
from contextlib import suppress
from dataclasses import dataclass, field

from ..app.kit_messages import KitRole
from ..app.peer_supervision import PeerDeadline, TimeoutPolicy
from .client import PeerClient
from .kit_envelopes import KitJson
from .transport_profiles import TransportEnvelopeProfile
from .wire_errors import TransportFailureError

Forward = Callable[[str, KitJson], Awaitable[None]]


@dataclass(slots=True)
class KitBackendRoutes:
    """One outbound session per role backend, opened lazily and closed together."""

    endpoints: Mapping[KitRole, str]
    deadline: float
    clients: dict[KitRole, PeerClient] = field(default_factory=dict)

    def forwarders(self) -> dict[KitRole, Forward]:
        """A forwarder per configured role, for the gateway to route through."""
        return {role: self._forwarder(role) for role in self.endpoints}

    def _forwarder(self, role: KitRole) -> Forward:
        async def forward(tool: str, arguments: KitJson) -> None:
            try:
                await (await self._client(role)).invoke(tool, arguments)
            except TransportFailureError:
                await self._discard(role)
                await (await self._client(role)).invoke(tool, arguments)

        return forward

    async def _client(self, role: KitRole) -> PeerClient:
        """The held session for *role*, opened on first use."""
        held = self.clients.get(role)
        if held is None:
            held = PeerClient(
                self.endpoints[role],
                PeerDeadline(TimeoutPolicy(self.deadline)),
                TransportEnvelopeProfile.KIT_EXTERNAL,
            )
            await held.__aenter__()
            self.clients[role] = held
        return held

    async def _discard(self, role: KitRole) -> None:
        """Drop a session that failed at the transport, so the next use reopens."""
        held = self.clients.pop(role, None)
        if held is not None:
            # A session that already died may fail to close; it is going away
            # either way, and its closing fault is not the caller's problem.
            with suppress(Exception):
                await held.__aexit__(None, None, None)

    async def close(self) -> None:
        """Close every session that was opened. Safe when none was."""
        held, self.clients = self.clients, {}
        for client in held.values():
            await client.__aexit__(None, None, None)
