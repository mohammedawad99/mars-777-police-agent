"""The outbound half of the protocol: cadence, and nothing else.

The inbound path has had a production owner since Stage 5-R3R. This is the side
that speaks first, and it is deliberately the thinnest thing that can be - every
value it sends is built by the owner that already owns it, and every decision it
would otherwise have to make is one somebody else already made.

**It sends what owners produced.** `Step0Runtime` builds the exchange, the
pregame runtime builds our proposal and lock evidence, `OutboundEvidenceRuntime`
seals the commitment and reveal, and `ResultExchange` owns the entire result
cadence. The runner never constructs a semantic value, never hashes, never draws
a nonce, never touches a rule and never reads a document it forwards.

**Commit, acknowledge and reveal are three operations, not one call.**
`send_commitment` returning means the request was delivered - not that the peer
agreed. The acknowledgement comes back later through *our* inbound server, so
the runner cannot know it has arrived except by asking the turn runtime that
recorded it. That is why the reveal is a separate method with a gate rather than
the second half of a single `perform_turn`, and why nothing here sleeps or polls.

**Lifecycle-scoped owners are resolved per call.** A turn runtime is consumed and
an evidence runtime is per sub-game, so both arrive as providers and neither is
captured. `ResultExchange` is a provider for a different reason: it is assembled
*from* six completed sub-games, so at the moment this runner is built it does not
truthfully exist yet. Only the two result methods resolve it, which is why an
agent can play its whole series before the result owner appears. The series audit
gate is series-scoped from the start, so it is held directly.
"""

from collections.abc import Callable
from dataclasses import dataclass

from ..domain.actions import PhysicalAction
from ..domain.negotiated_config import NegotiatedConfig
from .artifact_values import UtcTimestamp
from .declaration_values import Declaration
from .outbound_evidence_runtime import OutboundEvidenceRuntime
from .outbound_evidence_values import PreparedTurn
from .peer_transport import PeerTransportPort
from .pregame_session_runtime import PregameSessionRuntime
from .protocol_errors import StaleMessageError
from .result_exchange import ResultExchange
from .sealed_record_values import Intent, SealedState
from .series_audit_gate import SeriesAuditGate
from .step0_runtime import Step0Runtime
from .turn_cursor import TurnCursor
from .turn_protocol_runtime import TurnProtocolRuntime


@dataclass(frozen=True, slots=True)
class PeerRunner:
    """Outbound cadence over the peer transport. It owns no protocol state."""

    transport: PeerTransportPort
    step0: Step0Runtime
    pregame: PregameSessionRuntime
    turns: Callable[[], TurnProtocolRuntime]
    evidence: Callable[[], OutboundEvidenceRuntime]
    results: Callable[[], ResultExchange]
    series: SeriesAuditGate

    async def send_step0(self, declaration: Declaration) -> None:
        """Send our Step-0 exchange; the session it travels on is already open."""
        await self.transport.send_step0(self.step0.outbound(declaration))

    async def send_config_proposal(self, config: NegotiatedConfig) -> None:
        """Send our proposal for the current round, as the pregame owner built it."""
        await self.transport.send_config_proposal(self.pregame.prepare_proposal(config))

    async def send_config_lock(self) -> None:
        """Send lock evidence over the config this side adopted for the round."""
        await self.transport.send_config_lock(self.pregame.prepare_lock())

    async def open_turn(
        self,
        *,
        state: SealedState,
        action: PhysicalAction,
        intent: Intent,
        hint: str,
        cursor: TurnCursor,
    ) -> PreparedTurn:
        """Seal our turn, register the commitment locally, then send it.

        Registering before sending is the safe order: an acknowledgement that
        races back finds a commitment already recorded. The prepared turn is
        returned rather than kept - the caller holds it until the reveal, and it
        carries no nonce, state or intent to leak.
        """
        prepared = self.evidence().prepare_turn(
            state=state, action=action, intent=intent, hint=hint, cursor=cursor
        )
        self.turns().register_local_commitment(prepared.commitment)
        await self.transport.send_commitment(prepared.commitment)
        return prepared

    async def reveal_turn(self, prepared: PreparedTurn) -> bool:
        """Reveal our sealed turn once the peer has acknowledged it.

        The gate is the turn runtime's own record, not a flag kept here: only
        `accept_acknowledgement` sets it, and only after the digest matched what
        we registered. The returned `bool` is the peer's game-legality verdict,
        passed through exactly - a failure stays a failure.
        """
        turn = self.turns()
        registered = turn.local_commitment
        if not turn.local_acknowledged or registered is None:
            raise StaleMessageError("the peer has not acknowledged our commitment yet")
        if registered.h_commit != prepared.commitment.h_commit:
            raise StaleMessageError("this prepared turn is not the commitment we registered")
        return await self.transport.send_reveal(prepared.reveal)

    async def acknowledge_peer_turn(self) -> None:
        """Send the acknowledgement the turn runtime produced for the peer."""
        await self.transport.send_acknowledgement(self.turns().acknowledge())

    async def send_final_nonce_reveal(self) -> None:
        """Disclose this sub-game's nonces, exactly as the evidence owner batched them."""
        await self.transport.send_final_nonce_reveal(self.evidence().final_nonce_reveal())

    async def send_audit_disclosure(self) -> None:
        """Send our disclosure core unread - the runner never inspects it."""
        await self.transport.send_audit_disclosure(self.evidence().audit_disclosure())

    async def open_result_agreement(self) -> None:
        """Propose the result, once our whole series audit has passed."""
        results = self.results()
        results.require_series_audit(self.series)
        await results.open_agreement()

    async def respond_to_result(self, timestamp: UtcTimestamp) -> None:
        """Answer the proposer's request, under the same series audit gate."""
        results = self.results()
        results.require_series_audit(self.series)
        await results.send_response(timestamp)
