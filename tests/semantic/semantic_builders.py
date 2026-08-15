"""A real, legal sub-game - and the exact ways to make it a dishonest one.

Every value here is production-built: the sealed records come from a real
`OutboundEvidenceRuntime` over the real nonce source and the real SHA-256, the
peer's disclosure is rendered by the real writer, and the audit that receives it
is the real `AuditRuntime`. A test that wants a forgery therefore has to change
what the *game* says, not what the crypto says - which is the whole point of the
semantic layer.

The board is the locked one from the Appendix-F conforming config: a 7x7 grid
with the police at [0,0] and the thief at [3,3].
"""

from r16_builders import config

from mars777_police.app.audit_runtime import AuditRuntime
from mars777_police.app.audit_values import SubGameContext
from mars777_police.app.capture_transcript import CaptureRecord
from mars777_police.app.capture_values import CaptureAnswer, CaptureClaim, TurnOutcome
from mars777_police.app.outbound_evidence_runtime import OutboundEvidenceRuntime
from mars777_police.app.outbound_evidence_values import LocalEvidenceContext
from mars777_police.app.protocol_values import Sha256Digest
from mars777_police.app.sealed_record_values import ActorRole, Intent, SealedState
from mars777_police.app.semantic_review import rules_for
from mars777_police.app.turn_cursor import TurnCursor
from mars777_police.app.turn_protocol_state import TurnEvidence
from mars777_police.domain.actions import MoveAction, PhysicalAction
from mars777_police.domain.board import Position
from mars777_police.domain.rules import Move
from mars777_police.domain.scent_model_default import default_scent_model
from mars777_police.protocol.audit_commitment import CommitmentRecomputer
from mars777_police.protocol.secure_nonce import SecretsNonceSource

GAME_ID = "mars777-vs-groupx-2026w1-uid0001"
GAME_UID = "uid0001"
SUB_GAME = 1
CONFIG = config()
DIGEST = Sha256Digest("d" * 64)
PEER_GROUP = "GROUP-XY"
RULES = rules_for(CONFIG)
MODEL = default_scent_model()
"""The model a series locks; the review must be *given* it, never assume it."""
COP, THIEF = CONFIG.board_and_agents.cop_start, CONFIG.board_and_agents.thief_start


def evidence_for(role: ActorRole) -> OutboundEvidenceRuntime:
    """One side's real evidence producer for this sub-game."""
    return OutboundEvidenceRuntime(
        LocalEvidenceContext(GAME_ID, GAME_UID, SUB_GAME, DIGEST, role),
        SecretsNonceSource(),
        CommitmentRecomputer(),
    )


def audit_for(peer_role: ActorRole) -> AuditRuntime:
    """The audit owner that will receive that side's disclosure."""
    context = SubGameContext(GAME_ID, GAME_UID, SUB_GAME, DIGEST, peer_role, PEER_GROUP)
    return AuditRuntime(context, (), CommitmentRecomputer())


def seal(
    producer: OutboundEvidenceRuntime,
    step: int,
    cell: Position,
    action: PhysicalAction,
    barriers: tuple[Position, ...] = (),
) -> object:
    """Seal one turn of that side's play, exactly as a live turn would."""
    role = producer.context.role
    return producer.prepare_turn(
        state=SealedState(DIGEST, cell, barriers, step, role),
        action=action,
        intent=Intent.TRUTH,
        hint=f"step {step}",
        cursor=TurnCursor(SUB_GAME, step),
    )


def witness(prepared: object, accepted: bool = True) -> TurnEvidence:
    """What the other side's live turn runtime witnessed of that turn."""
    reveal = prepared.reveal  # type: ignore[attr-defined]
    commitment = prepared.commitment  # type: ignore[attr-defined]
    return TurnEvidence(reveal.cursor, commitment.h_commit, reveal.action, reveal.hint, accepted)


def row(step: int, answer: CaptureAnswer, claim: Position | None = None) -> CaptureRecord:
    """One capture row, as a live turn would have retained it."""
    return CaptureRecord(
        TurnCursor(SUB_GAME, step), None if claim is None else CaptureClaim(claim), answer
    )


def outcome(answer: CaptureAnswer) -> TurnOutcome:
    """The outcome a live reveal returned for that answer."""
    return TurnOutcome(True, answer)


NORTH = MoveAction(Move.N)
"""One ordinary legal move, used wherever the action itself is not the point."""


def audited(
    audit: AuditRuntime,
    peer: OutboundEvidenceRuntime,
    prepared: list[object],
    rows: tuple[CaptureRecord, ...] = (),
) -> AuditRuntime:
    """Drive the real audit cadence over the peer's real disclosure.

    *rows* are the answers we gave the peer's reveals, so they are the peer's
    outbound transcript and our inbound one - the same rows on both sides,
    which is exactly what the cross-check requires.
    """
    peer.observe_capture(rows)
    audit.observe(tuple(witness(one) for one in prepared), capture=rows)
    audit.accept_final_nonce_reveal(peer.final_nonce_reveal(), PEER_GROUP)
    audit.accept_audit_disclosure(peer.audit_disclosure())
    return audit
