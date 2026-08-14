"""The application owner of one live peer turn: commit, acknowledge, reveal.

Stage 4E-R18-R1-CR2 established that `Commitment`, `Acknowledgement` and
`Reveal` had no production owner at all - only test doubles stood behind the
transport. This is that owner.

**It does not open the commitment, and cannot.** The sealed record has eight
members; at reveal time three are still secret - the `nonce` until the final
nonce reveal, `state` and `intent` until the audit material - so there is nothing
to hash here. Ch 5 §5.3.2 / Figure 6 and §5.4 put the recomputation at the final
audit, which is what makes the scheme work: a peer may reveal inconsistent
material live and the proof arrives later. This runtime **correlates** instead -
this reveal belongs to the cursor whose commitment it recorded - and orders.

**An outcome is not a refusal.** `TurnOutcome` reports what a public fact
allowed and what the capture question answered; every protocol failure - wrong
phase, cursor, role, missing commitment, duplicate - raises instead, and
`E-HASH-MISMATCH` is unreachable here.

**It owns no game rule and no step counter.** Legality and truth belong to
`LocalTurnService` and `domain.truth`; the cursor advances from the
`completed_step` that service reports.

**Acknowledgements are retained, not re-validated.** Both directions append one
`AckEvidence` *after* the existing checks pass, so a stale or mismatched
acknowledgement can never leave a log event behind.

**The posture is part of the contract.** `..._SCENT_V2` reveals carry one
emission and pre-V2 reveals carry none; `require_scent_shape` refuses either
violation as malformed, and what arrives is retained, never recomputed."""

from dataclasses import dataclass, field, replace

from ..domain.truth import LocalTruth
from .capture_observation import observe_reveal, require_claim_shape
from .capture_transcript import TurnTranscript
from .capture_values import TurnOutcome
from .interop_profiles import CompatibilityProfile
from .peer_turn_messages import Acknowledgement, Commitment, Reveal
from .protocol_errors import StaleMessageError
from .sealed_record_values import ActorRole
from .turn_cursor import TurnCursor
from .turn_protocol_state import AckEvidence, PendingCommitment, TurnEvidence, TurnPhase
from .turn_scent_contract import SCENT_POSTURE, require_scent_shape
from .turn_service import LocalTurnService


def _refuse(reason: str) -> StaleMessageError:
    return StaleMessageError(reason)


@dataclass(slots=True)
class TurnProtocolRuntime:
    """One peer's live turn sequencing against one opponent."""

    role: ActorRole
    turns: LocalTurnService
    truth: LocalTruth
    cursor: TurnCursor
    phase: TurnPhase = field(default=TurnPhase.AWAITING_COMMITMENT)
    peer_commitment: PendingCommitment | None = field(default=None)
    local_commitment: PendingCommitment | None = field(default=None)
    local_acknowledged: bool = field(default=False)
    evidence: tuple[TurnEvidence, ...] = field(default=())
    acks: tuple[AckEvidence, ...] = field(default=())
    capture: TurnTranscript = field(default_factory=TurnTranscript)
    posture: CompatibilityProfile = field(default=SCENT_POSTURE)
    """The negotiated turn contract this session speaks; V2 requires scent."""

    @property
    def peer_role(self) -> ActorRole:
        """The other side's config-locked role - the game has exactly two."""
        return ActorRole.THIEF if self.role is ActorRole.POLICE else ActorRole.POLICE

    def _require_cursor(self, cursor: TurnCursor, what: str) -> None:
        if cursor != self.cursor:
            raise _refuse(f"{what} carries {cursor}, not the expected {self.cursor}")

    def accept_commitment(self, commitment: Commitment) -> None:
        """Record the peer's sealed digest for this cursor. Nothing is opened."""
        if self.phase is not TurnPhase.AWAITING_COMMITMENT:
            raise _refuse(f"a commitment cannot arrive while {self.phase.value}")
        self._require_cursor(commitment.cursor, "commitment")
        self.peer_commitment = PendingCommitment(commitment.cursor, commitment.h_commit)
        self.phase = TurnPhase.AWAITING_OUR_ACKNOWLEDGEMENT

    def acknowledge(self) -> Acknowledgement:
        """Lock the peer's commitment and return the acknowledgement to send."""
        pending = self.peer_commitment
        if self.phase is not TurnPhase.AWAITING_OUR_ACKNOWLEDGEMENT or pending is None:
            raise _refuse(f"nothing to acknowledge while {self.phase.value}")
        self.phase = TurnPhase.AWAITING_REVEAL
        self.acks += (AckEvidence(pending.cursor, pending.h_commit, self.role),)
        return Acknowledgement(pending.cursor, pending.h_commit)

    def register_local_commitment(self, commitment: Commitment) -> None:
        """Record our own outgoing commitment so the peer's ack can be matched."""
        self._require_cursor(commitment.cursor, "our commitment")
        if self.local_commitment is not None:
            raise _refuse("our commitment for this cursor was already registered")
        self.local_commitment = PendingCommitment(commitment.cursor, commitment.h_commit)

    def accept_acknowledgement(self, acknowledgement: Acknowledgement) -> None:
        """Record the peer's acknowledgement of **our** commitment."""
        pending = self.local_commitment
        if pending is None:
            raise _refuse("an acknowledgement arrived with no commitment of ours pending")
        if self.local_acknowledged:
            raise _refuse("our commitment was already acknowledged")
        self._require_cursor(acknowledgement.cursor, "acknowledgement")
        if acknowledgement.h_commit != pending.h_commit:
            raise _refuse("the acknowledgement does not carry our committed digest")
        self.local_acknowledged = True
        self.acks += (AckEvidence(pending.cursor, pending.h_commit, self.peer_role),)

    def accept_reveal(self, reveal: Reveal) -> TurnOutcome:
        """Observe the peer's reveal and answer what we can honestly know.

        Two things this deliberately does **not** do. It never applies the peer's
        action to our own truth - moving our piece with it was the defect R8
        removed - and it never claims their action was spatially legal: their
        pre-action cell is sealed until the final audit.
        """
        pending = self.peer_commitment
        if self.phase is not TurnPhase.AWAITING_REVEAL or pending is None:
            raise _refuse(f"a reveal cannot arrive while {self.phase.value}")
        self._require_cursor(reveal.cursor, "reveal")
        require_claim_shape(reveal, self.peer_role, _refuse)
        require_scent_shape(reveal, self.posture)
        outcome, self.truth = observe_reveal(reveal, self.truth)
        witnessed = TurnEvidence(
            pending.cursor, pending.h_commit, reveal.action, reveal.hint, outcome.accepted
        )
        self.evidence += (replace(witnessed, scent=reveal.scent_emission),)
        self.capture.observe_inbound(reveal, outcome)
        self.phase = TurnPhase.CONSUMED
        return outcome

    def observe_outgoing(self, reveal: Reveal, outcome: TurnOutcome) -> None:
        """Retain what the peer answered **our** reveal, once the call returned.

        Only the caller that completed the transport invocation may record it: a
        guessed answer is the fabrication the audit cross-check exists to catch.
        """
        self.capture.observe_outgoing(reveal, outcome)

    @property
    def audit_required(self) -> bool:
        """Whether a declared capture ended ordinary play, however it was answered."""
        return self.capture.declared
