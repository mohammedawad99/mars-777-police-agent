"""The application owner of our own commit-reveal evidence for one sub-game.

Stage 5-R4 stopped here: the agent could verify a peer's commitment but could
not make one of its own. `Commitment` and `FinalNonceReveal` were constructed
nowhere in production except the inbound decoders, no nonce generator existed,
and nothing retained the three sealed members that stay secret during play. This
is the producer that closes all three.

**It is not `TurnProtocolRuntime`, and must not become it.** That runtime owns
the live cadence and deliberately holds no secret - Stage 5-R1 made `TurnEvidence`
carry only what the audit needs about the *peer*. Our nonce, sealed state and
intent are a different thing with a different lifetime, so they live here, behind
a lifecycle that cannot hand them out early.

**The nonce is the whole reason for the phases.** `OPEN` accepts new turns;
sealing the final nonce reveal ends that, because a turn committed after the
opponent has our nonces is a turn we could have chosen knowing what they hold.
After the disclosure the runtime is terminal - the next sub-game gets a new one.

It computes no digest, opens no socket, reads no clock and touches no file: the
hash comes from `CommitmentPort` and the nonce from `NonceSourcePort`.
"""

from dataclasses import dataclass, field

from ..domain.actions import PhysicalAction
from ..domain.scent_emission import ScentEmission
from .audit_disclosure_writer import AuditDocument, document
from .capture_observation import require_claim_shape
from .capture_transcript import CaptureRecord
from .capture_values import CaptureClaim
from .nonce_source import NonceSourcePort
from .outbound_evidence_values import (
    EvidencePhase,
    LocalEvidenceContext,
    PreparedTurn,
    SealedTurnRecord,
)
from .peer_final_messages import FinalNonceReveal, NonceRevealEntry
from .peer_turn_messages import Commitment, Reveal
from .ports import CommitmentPort
from .protocol_errors import LocalDefectError, StaleMessageError
from .sealed_record_values import Intent, SealedState
from .turn_cursor import TurnCursor


@dataclass(slots=True)
class OutboundEvidenceRuntime:
    """Our private sealed turns for one sub-game, from commitment to disclosure."""

    context: LocalEvidenceContext
    nonces: NonceSourcePort
    commitments: CommitmentPort
    phase: EvidencePhase = field(default=EvidencePhase.OPEN)
    records: tuple[SealedTurnRecord, ...] = field(default=())
    capture: tuple[CaptureRecord, ...] = field(default=())

    @property
    def ordered(self) -> tuple[SealedTurnRecord, ...]:
        """Our sealed turns in step order - the one order we ever disclose in."""
        return tuple(sorted(self.records, key=lambda record: record.cursor.step))

    def prepare_turn(
        self,
        *,
        state: SealedState,
        action: PhysicalAction,
        intent: Intent,
        hint: str,
        cursor: TurnCursor,
        claim: CaptureClaim | None = None,
        scent: ScentEmission | None = None,
    ) -> PreparedTurn:
        """Seal one turn of ours and return only what a peer may receive.

        The nonce is drawn, used and kept; what comes back is the commitment and
        the reveal, so the caller cannot disclose early even by mistake.

        *claim* is one of the two reveal members that are **not** sealed: it is a
        question about a cell only the opponent knows, so there is nothing of
        ours to commit to. It is checked against the same shape rule the
        receiver applies, so we cannot send a declaration a peer must refuse.

        *scent* is the other. It is **passed through, never computed here**: this
        owner holds nonces and digests, not the board, and deriving an emission
        would mean applying a game action inside the evidence owner. The runner
        projects it from the same action and hands it in.
        """
        if self.phase is not EvidencePhase.OPEN:
            raise StaleMessageError(f"no turn may be prepared while {self.phase.value}")
        self._require_cursor(cursor)
        reveal = Reveal(cursor, action, hint, claim, scent)
        require_claim_shape(reveal, self.context.role, LocalDefectError)
        if state.role is not self.context.role:
            raise LocalDefectError(
                f"sealed state names {state.role.value!r}, not our own {self.context.role.value!r}",
            )
        nonce = self.nonces.fresh()
        if any(record.nonce == nonce for record in self.records):
            raise LocalDefectError("the nonce source returned one already used this sub-game")
        commit = self.commitments.recompute(
            state=state,
            action=action,
            intent=intent,
            hint=hint,
            cursor=cursor,
            role=self.context.role,
            nonce=nonce,
        )
        self.records += (SealedTurnRecord(cursor, state, action, intent, hint, nonce, commit),)
        return PreparedTurn(Commitment(cursor, commit), reveal)

    def _require_cursor(self, cursor: TurnCursor) -> None:
        """Refuse another sub-game's turn, and refuse the same turn twice."""
        if cursor.sub_game != self.context.sub_game:
            raise LocalDefectError(
                f"cursor names sub-game {cursor.sub_game},"
                f" not this runtime's {self.context.sub_game}",
            )
        if any(record.cursor == cursor for record in self.records):
            raise LocalDefectError(f"{cursor} was already prepared for this sub-game")

    def final_nonce_reveal(self) -> FinalNonceReveal:
        """Disclose our nonces and close turn preparation for this sub-game.

        Rebuilt from the retained records every time, so a repeat call returns
        the same associations rather than drawing anything new.
        """
        if self.phase is EvidencePhase.OPEN:
            self.phase = EvidencePhase.NONCES_DISCLOSED
        return FinalNonceReveal(
            tuple(NonceRevealEntry(record.cursor, record.nonce) for record in self.ordered)
        )

    def observe_capture(self, capture: tuple[CaptureRecord, ...]) -> None:
        """Adopt what our own finished reveals asked and were answered."""
        if self.phase is EvidencePhase.COMPLETE:
            raise StaleMessageError("this sub-game's disclosure was already rendered")
        self.capture += capture

    def audit_disclosure(self) -> AuditDocument:
        """Render our disclosure core, once the nonces are already disclosed.

        The capture rows are what our own reveals asked and were answered; the
        peer checks them against the answers it actually gave.
        """
        if self.phase is EvidencePhase.OPEN:
            raise StaleMessageError("the audit disclosure follows the final nonce reveal")
        self.phase = EvidencePhase.COMPLETE
        return document(self.context, self.ordered, self.capture)
