"""The application owner of one completed sub-game's final audit.

This is the commitment correspondence deferred by Stage 5-R1-R1: reveal cannot
open a commitment while three sealed members are secret, so Ch 5 §5.4 discloses
logs and nonces at the end and recomputes SHA-256 here.

**Live evidence outranks the document.** Every member also witnessed live -
`commit`, `move`, `hint`, `role`, `step`, and the never-sealed capture and scent
rows - must agree exactly before anything is hashed, and that evidence is adopted
turn by turn, before any nonce arrives. **The peer's verdict has no standing**:
our annotations are derived here, sent nowhere."""

from dataclasses import dataclass, field

from .audit_capture import capture_rows
from .audit_disclosure import turns
from .audit_milestones import AuditMilestones
from .audit_scent import scent_rows
from .audit_values import AuditOutcome, AuditPhase, SubGameContext, require_aggregate
from .audit_verification import by_cursor, require_identity, verdict_for
from .capture_transcript import CaptureRecord, require_same_scent, require_same_transcript
from .peer_final_messages import FinalNonceReveal
from .ports import CommitmentPort
from .protocol_errors import StaleMessageError
from .protocol_values import FinalAuditVerdict, NonceValue
from .scent_records import ScentRecord
from .semantic_values import CONSISTENT, SemanticFinding
from .turn_cursor import TurnCursor
from .turn_protocol_state import AckEvidence, TurnEvidence


@dataclass(slots=True)
class AuditRuntime:
    """Final audit for exactly one sub-game, from nonce batch to local verdict."""

    context: SubGameContext
    evidence: tuple[TurnEvidence, ...]
    commitments: CommitmentPort
    phase: AuditPhase = field(default=AuditPhase.AWAITING_NONCES)
    nonces: dict[TurnCursor, NonceValue] = field(default_factory=dict)
    outcome: AuditOutcome | None = field(default=None)
    disclosure: dict[str, object] | None = field(default=None)  # retained for the log
    acks: tuple[AckEvidence, ...] = field(default=())  # log attribution, never audited
    capture: tuple[CaptureRecord, ...] = field(default=())  # what we watched happen
    semantic: SemanticFinding = field(default=CONSISTENT)  # the replay's finding
    milestones: AuditMilestones = field(default_factory=AuditMilestones)  # set last, never truth

    def __post_init__(self) -> None:
        require_aggregate(self.evidence, self.context.sub_game)

    def observe(
        self,
        evidence: tuple[TurnEvidence, ...],
        acks: tuple[AckEvidence, ...] = (),
        capture: tuple[CaptureRecord, ...] = (),
    ) -> None:
        """Adopt a finished turn's evidence, its acks and what it asked about capture."""
        if self.phase is not AuditPhase.AWAITING_NONCES:
            raise StaleMessageError(f"a turn cannot be observed while {self.phase.value}")
        require_aggregate(self.evidence + evidence, self.context.sub_game)
        self.evidence += evidence
        self.acks += acks
        self.capture += capture

    @property
    def expected(self) -> tuple[TurnCursor, ...]:
        """The cursors this sub-game played, in step order."""
        return tuple(sorted((r.cursor for r in self.evidence), key=lambda c: c.step))

    @property
    def expected_scent(self) -> tuple[ScentRecord, ...]:
        """The emissions the peer sent us, projected from the live evidence.

        Derived rather than stored again, so no second history can drift from
        `TurnEvidence.scent`. A pre-V2 turn carried none and adds no row."""
        return tuple(
            ScentRecord(one.cursor, one.scent) for one in self.evidence if one.scent is not None
        )

    def accept_final_nonce_reveal(self, reveal: FinalNonceReveal, sender_id: str) -> None:
        """Adopt the peer's batched nonce disclosure for this sub-game."""
        if self.phase is not AuditPhase.AWAITING_NONCES:
            raise StaleMessageError(f"a nonce batch cannot arrive while {self.phase.value}")
        if sender_id != self.context.peer_group_id:
            raise StaleMessageError("the nonce batch did not come from the expected peer")
        cursors = [entry.cursor for entry in reveal.entries]
        if len(set(cursors)) != len(cursors):
            raise StaleMessageError("the nonce batch repeats a cursor")
        if tuple(sorted(cursors, key=lambda c: c.step)) != self.expected:
            raise StaleMessageError("the nonce batch does not match the played turns")
        self.nonces = {entry.cursor: entry.nonce for entry in reveal.entries}
        self.phase = AuditPhase.AWAITING_DISCLOSURE

    def accept_audit_disclosure(self, document: dict[str, object]) -> None:
        """Verify the peer's disclosed log against what we already witnessed."""
        if self.phase is not AuditPhase.AWAITING_DISCLOSURE:
            raise StaleMessageError(f"a disclosure cannot arrive while {self.phase.value}")
        require_identity(document, self.context)
        require_same_transcript(self.capture, capture_rows(document))
        require_same_scent(self.expected_scent, scent_rows(document))
        indexed = by_cursor(turns(document), self.expected)
        self.outcome = verdict_for(
            self.evidence, indexed, self.nonces, self.context.peer_role, self.commitments
        )
        self.disclosure = dict(document)
        self.phase = AuditPhase.COMPLETE
        self.milestones.complete.set()

    def adopt_semantic(self, finding: SemanticFinding) -> None:
        """Adopt the replay's finding about the log this audit just verified.

        Only after the disclosure: the replay needs the peer's own positions,
        and those arrive with it. Once, because a second finding would be a
        second answer to a question this sub-game has already answered.
        """
        if self.phase is not AuditPhase.COMPLETE:
            raise StaleMessageError(f"a semantic finding cannot arrive while {self.phase.value}")
        if not self.semantic.consistent:
            raise StaleMessageError("this sub-game was already reviewed")
        self.semantic = finding

    @property
    def recorded_outcome(self) -> AuditOutcome:
        """The outcome the series records: the hashes **and** the replay.

        A forged story that hashes correctly is still a forgery, so a tampering
        finding decides the outcome at the step it names. A false capture claim
        is not tampering and leaves this untouched - it is scored, not blocked.
        """
        outcome = self.outcome
        if outcome is None:
            raise StaleMessageError("this sub-game has not been audited")
        if self.semantic.honest:
            return outcome
        return AuditOutcome(FinalAuditVerdict.TAMPERED, self.semantic.step)

    @property
    def verdict(self) -> FinalAuditVerdict | None:
        """The local verdict, `None` until the audit completes."""
        return None if self.outcome is None else self.recorded_outcome.verdict

    @property
    def verified(self) -> bool:
        """Whether result agreement may proceed for this sub-game."""
        return self.outcome is not None and self.recorded_outcome.verified
