"""The application owner of one live peer turn: commit, acknowledge, reveal.

Stage 4E-R18-R1-CR2 established that `Commitment`, `Acknowledgement` and
`Reveal` had no production owner at all - only test doubles stood behind the
transport. This is that owner.

**It does not open the commitment, and cannot.** The sealed record has eight
members; at reveal time three of them are still secret - the `nonce` until the
final nonce reveal, and `state` and `intent` until the audit material. So there
is nothing to hash here, and `compute_commitment`/`commitment_matches` are not
called. Ch 5 §5.3.2 / Figure 6 and Ch 5 §5.4 put the recomputation at the final
audit, which is exactly what makes the scheme work: a peer may reveal
inconsistent material during live play and the proof arrives later. What this
runtime does instead is **correlate** - this reveal belongs to the cursor whose
commitment and acknowledgement it already recorded - and enforce ordering.

**An outcome is not a refusal.** `TurnOutcome` reports what a public fact
allowed and what the capture question answered; every protocol failure - wrong
phase, wrong cursor, wrong role, no commitment, a duplicate - raises instead.
Returning one for the other would tell a caller "you played illegally" when the
truth is "you are out of order", and `E-HASH-MISMATCH` is unreachable here.

**It owns no game rule and no step counter.** Legality and truth belong to
`LocalTurnService` and `domain.truth`; the cursor advances from the
`completed_step` that service reports, so there is no second source of truth.

**Acknowledgements are retained, not re-validated.** Both directions append one
`AckEvidence` *after* the existing checks pass, so a stale, duplicated or
mismatched acknowledgement - which raises above - can never leave a log event
behind. Nothing is added to the wire message: the acking role is this runtime's
own locked role, or its complement.
"""

from dataclasses import dataclass, field

from ..domain.truth import LocalTruth
from .capture_observation import observe_reveal, require_claim_shape
from .capture_transcript import TurnTranscript
from .capture_values import TurnOutcome
from .peer_turn_messages import Acknowledgement, Commitment, Reveal
from .protocol_errors import StaleMessageError
from .sealed_record_values import ActorRole
from .turn_cursor import TurnCursor
from .turn_protocol_state import AckEvidence, PendingCommitment, TurnEvidence, TurnPhase
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

        Two things this deliberately does **not** do. It never applies the
        peer's action to our own truth - their move is theirs, and moving our
        piece with it was the defect R8 removed. And it never claims their
        action was spatially legal: their pre-action cell is sealed until the
        final audit, so `accepted` reports public facts only.
        """
        pending = self.peer_commitment
        if self.phase is not TurnPhase.AWAITING_REVEAL or pending is None:
            raise _refuse(f"a reveal cannot arrive while {self.phase.value}")
        self._require_cursor(reveal.cursor, "reveal")
        require_claim_shape(reveal, self.peer_role, _refuse)
        outcome, self.truth = observe_reveal(reveal, self.truth)
        self.evidence += (
            TurnEvidence(
                pending.cursor, pending.h_commit, reveal.action, reveal.hint, outcome.accepted
            ),
        )
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
