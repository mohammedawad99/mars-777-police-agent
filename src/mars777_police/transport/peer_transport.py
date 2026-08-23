"""The FastMCP adapter that satisfies `PeerTransportPort`.

`PeerClient` owns the wire — connection, envelope, per-call deadline, response
decoding, framework-error translation. This class is the semantic face of it:
it takes the project's own values, encodes each one with the codec that already
owns its family, and hands the result back as a semantic value.

The split is deliberate. Keeping encoding here rather than in `PeerClient` means
the port the application depends on never mentions a DTO, and `PeerClient` stays
a transport concern that knows nothing about which family it is carrying.

Conformance is **structural**: `app.peer_transport.PeerTransportPort` is a
`Protocol`, this class implements it without importing it, and a strict static
check proves the match with no `cast` and no `type: ignore`.
"""

from contextlib import suppress

from ..app.capture_values import TurnOutcome
from ..app.peer_final_messages import FinalNonceReveal, ResultAgreement
from ..app.peer_pregame_messages import (
    ConfigLockEvidence,
    ConfigProposal,
    Step0DeclarationExchange,
)
from ..app.peer_transport import AuditDocument
from ..app.peer_turn_messages import Acknowledgement, Commitment, Reveal
from ..app.protocol_values import Sha256Digest
from .call_arguments import KitOutbound, kit_call
from .client import PeerClient
from .codec_declaration import encode_step0
from .codec_final import encode_final_nonce, encode_result_agreement
from .codec_pregame import encode_lock, encode_proposal
from .codec_turn import encode_acknowledgement, encode_commitment, encode_reveal


class FastMcpPeerTransport:
    """The concrete outbound peer transport, over one peer's stable ingress."""

    def __init__(self, client: PeerClient) -> None:
        self._client = client

    @property
    def url(self) -> str:
        """The peer endpoint this transport speaks to."""
        return self._client.url

    async def send_kit(self, message: KitOutbound) -> None:
        """Send one pinned kit message, through the client's own held session.

        The tool name and the argument name come from the message's own type,
        so the pinned asymmetry cannot be spelled wrong at a call site, and a
        client built for the internal wire refuses to build these arguments at
        all rather than putting a shape on the wire its own server would reject.
        """
        tool, request = kit_call(message, self._client.profile)
        await self._client.invoke(tool, request)

    async def send_settlement(self, envelope: dict[str, object]) -> None:
        """Send one series settlement envelope, as raw arguments.

        Deliberately not built by the typed KIT encoder: this is a settlement,
        not a sub-game disclosure, and it carries a digest instead of a chain.
        Routing it through the disclosure encoder would mean teaching that
        encoder to omit the very thing it exists to render.

        A send failure is swallowed on purpose - the exchange resends on its own
        cadence until the agreed window closes, and one refused attempt against
        a peer that has not finished its last sub-game is expected, not a fault.
        """
        with suppress(Exception):
            await self._client.invoke("submit_audit", {"payload": envelope})

    async def send_step0(self, exchange: Step0DeclarationExchange) -> None:
        """Send our Step-0 declaration and its keyed proof."""
        await self._client.complete("negotiate", "step0", encode_step0(exchange))

    async def send_config_proposal(self, proposal: ConfigProposal) -> None:
        """Send a complete config proposal for the current sub-game."""
        await self._client.complete("negotiate", "config_proposal", encode_proposal(proposal))

    async def send_config_lock(self, evidence: ConfigLockEvidence) -> None:
        """Send our authenticated config-lock evidence."""
        await self._client.complete("negotiate", "config_lock", encode_lock(evidence))

    async def send_commitment(self, commitment: Commitment) -> None:
        """Send this turn's sealed commitment."""
        await self._client.complete("receive_turn", "commitment", encode_commitment(commitment))

    async def send_acknowledgement(self, acknowledgement: Acknowledgement) -> None:
        """Acknowledge the peer's commitment."""
        await self._client.complete(
            "receive_turn", "acknowledgement", encode_acknowledgement(acknowledgement)
        )

    async def send_reveal(self, reveal: Reveal) -> TurnOutcome:
        """Send our reveal and return the outcome the peer reported."""
        outcome: TurnOutcome = await self._client.outcome(encode_reveal(reveal))
        return outcome

    async def send_final_nonce_reveal(self, disclosure: FinalNonceReveal) -> None:
        """Send the batched end-of-sub-game nonce disclosure."""
        await self._client.complete(
            "submit_audit", "final_nonce_reveal", encode_final_nonce(disclosure)
        )

    async def send_audit_disclosure(self, document: AuditDocument) -> None:
        """Send our JSON-native audit-disclosure document."""
        await self._client.complete("submit_audit", "audit_disclosure", document)

    async def send_result_agreement(self, agreement: ResultAgreement) -> Sha256Digest:
        """Send our single result agreement and return the peer's digest."""
        return await self._client.digest(encode_result_agreement(agreement))
