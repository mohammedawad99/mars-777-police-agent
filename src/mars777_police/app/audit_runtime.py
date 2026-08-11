"""The application owner of one completed sub-game's final audit.

This is where the commitment correspondence deferred by Stage 5-R1-R1 happens.
Ordinary reveal could not open a commitment - three of the eight sealed members
were still secret - so Ch 5 §5.4 has both sides disclose logs and nonces at the
end, rebuild the opponent's committed data and recompute SHA-256.

**Live evidence outranks the document, and contradicting it is fatal.** Every
member also witnessed live - `commit`, `move`, `hint`, `role`, `step` - must
agree exactly before anything is hashed, so a log rewritten into internal
self-consistency still fails. `audit_disclosure` has already parsed the move into
a `PhysicalAction`, so that comparison is **domain-value equality** rather than
two dictionaries matched through a cryptographic port.

**The peer's verdict has no standing.** `entries[].verified`, `audit.result` and
`audit.tampered_step` are LOCAL-DERIVED-AUDIT; this runtime derives them itself,
transmits nothing, and assigns no sanction or score.
"""

from dataclasses import dataclass, field

from ..domain.actions import BarrierAction, MoveAction
from .audit_disclosure import DisclosedTurn, identity, turns
from .audit_values import AuditOutcome, AuditPhase, SubGameContext
from .peer_final_messages import FinalNonceReveal
from .ports import CommitmentPort
from .protocol_errors import StaleMessageError
from .protocol_values import FinalAuditVerdict, NonceValue, Sha256Digest
from .sealed_record_values import Intent, SealedState
from .turn_cursor import TurnCursor
from .turn_protocol_state import TurnEvidence


@dataclass(slots=True)
class AuditRuntime:
    """Final audit for exactly one sub-game, from nonce batch to local verdict."""

    context: SubGameContext
    evidence: tuple[TurnEvidence, ...]
    commitments: CommitmentPort
    phase: AuditPhase = field(default=AuditPhase.AWAITING_NONCES)
    nonces: dict[TurnCursor, NonceValue] = field(default_factory=dict)
    outcome: AuditOutcome | None = field(default=None)

    def __post_init__(self) -> None:
        seen = [record.cursor for record in self.evidence]
        if len(set(seen)) != len(seen):
            raise ValueError("the evidence aggregate carries a duplicate cursor")
        if any(cursor.sub_game != self.context.sub_game for cursor in seen):
            raise ValueError("every evidence cursor must belong to this sub-game")

    @property
    def expected(self) -> tuple[TurnCursor, ...]:
        """The cursors this sub-game played, in step order."""
        return tuple(sorted((r.cursor for r in self.evidence), key=lambda c: c.step))

    def accept_final_nonce_reveal(self, disclosure: FinalNonceReveal, sender_id: str) -> None:
        """Adopt the peer's batched nonce disclosure for this sub-game."""
        if self.phase is not AuditPhase.AWAITING_NONCES:
            raise StaleMessageError(f"a nonce batch cannot arrive while {self.phase.value}")
        if sender_id != self.context.peer_group_id:
            raise StaleMessageError("the nonce batch did not come from the expected peer")
        cursors = [entry.cursor for entry in disclosure.entries]
        if len(set(cursors)) != len(cursors):
            raise StaleMessageError("the nonce batch repeats a cursor")
        if tuple(sorted(cursors, key=lambda c: c.step)) != self.expected:
            raise StaleMessageError("the nonce batch does not match the played turns")
        self.nonces = {entry.cursor: entry.nonce for entry in disclosure.entries}
        self.phase = AuditPhase.AWAITING_DISCLOSURE

    def accept_audit_disclosure(self, document: dict[str, object]) -> None:
        """Verify the peer's disclosed log against what we already witnessed."""
        if self.phase is not AuditPhase.AWAITING_DISCLOSURE:
            raise StaleMessageError(f"a disclosure cannot arrive while {self.phase.value}")
        self._require_identity(document)
        disclosed = self._by_cursor(turns(document))
        self.outcome = self._verdict(disclosed)
        self.phase = AuditPhase.COMPLETE

    def _require_identity(self, document: dict[str, object]) -> None:
        game_id, game_uid, sub_game, config = identity(document)
        expected = (
            self.context.game_id,
            self.context.game_uid,
            self.context.sub_game,
            self.context.config_sha256.value,
        )
        if (game_id, game_uid, sub_game, config) != expected:
            raise StaleMessageError("the disclosed log is not this sub-game's")

    def _by_cursor(self, disclosed: tuple[DisclosedTurn, ...]) -> dict[TurnCursor, DisclosedTurn]:
        indexed: dict[TurnCursor, DisclosedTurn] = {}
        for turn in disclosed:
            cursor = TurnCursor(turn.sub_game, turn.step)
            if cursor in indexed:
                raise StaleMessageError("the disclosed log repeats a turn")
            indexed[cursor] = turn
        if tuple(sorted(indexed, key=lambda c: c.step)) != self.expected:
            raise StaleMessageError("the disclosed log does not match the played turns")
        return indexed

    def _verdict(self, indexed: dict[TurnCursor, DisclosedTurn]) -> AuditOutcome:
        for record in sorted(self.evidence, key=lambda r: r.cursor.step):
            if not self._turn_verifies(record, indexed[record.cursor]):
                return AuditOutcome(FinalAuditVerdict.TAMPERED, record.cursor.step)
        return AuditOutcome(FinalAuditVerdict.VERIFIED_OK)

    def _turn_verifies(self, live: TurnEvidence, turn: DisclosedTurn) -> bool:
        """Cross-check the log against live facts, then recompute the digest."""
        action, peer = live.action, self.context.peer_role
        if not isinstance(action, MoveAction | BarrierAction):
            return False
        disclosed = (turn.commit, turn.hint, turn.role, turn.step, turn.move)
        if disclosed != (live.h_commit.value, live.hint, peer.value, live.cursor.step, action):
            return False
        try:
            state = SealedState(
                Sha256Digest(turn.config_sha256), turn.self_pos, turn.barriers, turn.step, peer
            )
            intent = Intent(turn.intent)
        except ValueError:
            return False
        recomputed = self.commitments.recompute(
            state=state,
            action=action,
            intent=intent,
            hint=live.hint,
            cursor=live.cursor,
            role=peer,
            nonce=self.nonces[live.cursor],
        )
        return self.commitments.matches(live.h_commit, recomputed)

    @property
    def verdict(self) -> FinalAuditVerdict | None:
        """The local verdict, or `None` until the audit completes."""
        return self.outcome.verdict if self.outcome is not None else None

    @property
    def verified(self) -> bool:
        """Whether result agreement may proceed for this sub-game."""
        return self.outcome is not None and self.outcome.verified
