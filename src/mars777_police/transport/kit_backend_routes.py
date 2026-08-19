"""The gateway's outbound half: one held session to each private role backend.

The gateway routes; these are the wires it routes over. One `PeerClient` per
role, opened once and held for the series, because a session re-established per
call is the failure Stage 4E measured over a real tunnel - thirty operations
each opening their own session failed from the twenty-first onward.

**Private, and they stay private.** These endpoints are local implementation
detail: they are never advertised to a peer, never written into a declaration
and never printed in the operator banner. The only address anybody outside this
process learns is the group's one public route.
"""

from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass, field

from ..app.kit_messages import KitRole
from ..app.peer_supervision import PeerDeadline, TimeoutPolicy
from .client import PeerClient
from .kit_envelopes import KitJson
from .transport_profiles import TransportEnvelopeProfile

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

    async def close(self) -> None:
        """Close every session that was opened. Safe when none was."""
        held, self.clients = self.clients, {}
        for client in held.values():
            await client.__aexit__(None, None, None)
