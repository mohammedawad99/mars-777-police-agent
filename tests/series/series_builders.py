"""Real six-sub-game audits, built from the real producer and real receiver."""

import evidence_builders as evidence
from evidence_builders import PEER_GROUP

from mars777_police.app.audit_runtime import AuditRuntime
from mars777_police.app.audit_values import SubGameContext
from mars777_police.app.outbound_evidence_runtime import OutboundEvidenceRuntime
from mars777_police.app.outbound_evidence_values import LocalEvidenceContext
from mars777_police.app.sealed_record_values import Intent, SealedState
from mars777_police.app.turn_cursor import TurnCursor
from mars777_police.app.turn_protocol_state import TurnEvidence
from mars777_police.domain.actions import MoveAction
from mars777_police.domain.rules import Move
from mars777_police.protocol.audit_commitment import CommitmentRecomputer
from mars777_police.protocol.secure_nonce import SecretsNonceSource

HINT = "moving north"


def audit_of(sub_game: int, *, tampered: bool = False) -> AuditRuntime:
    """One real sub-game audit, driven producer → receiver end to end.

    *tampered* rewrites the hint in the disclosed copy only, so the receiver's
    own recomputation is what decides - never a fabricated outcome.
    """
    producer = OutboundEvidenceRuntime(
        LocalEvidenceContext(
            evidence.GAME_ID, evidence.GAME_UID, sub_game, evidence.CONFIG, evidence.OURS
        ),
        SecretsNonceSource(),
        CommitmentRecomputer(),
    )
    cursor = TurnCursor(sub_game, 1)
    turn = producer.prepare_turn(
        state=SealedState(evidence.CONFIG, evidence.POS[1], (), 1, evidence.OURS),
        action=MoveAction(Move.N),
        intent=Intent.TRUTH,
        hint=HINT,
        cursor=cursor,
    )
    live = (
        TurnEvidence(cursor, turn.commitment.h_commit, turn.reveal.action, turn.reveal.hint, True),
    )
    receiver = AuditRuntime(
        SubGameContext(
            evidence.GAME_ID,
            evidence.GAME_UID,
            sub_game,
            evidence.CONFIG,
            evidence.OURS,
            PEER_GROUP,
        ),
        live,
        CommitmentRecomputer(),
    )
    receiver.accept_final_nonce_reveal(producer.final_nonce_reveal(), PEER_GROUP)
    document = producer.audit_disclosure()
    if tampered:
        document["entries"][0]["hint"] = "a hint that was never sealed"  # type: ignore[index]
    receiver.accept_audit_disclosure(document)
    return receiver


def series(order: tuple[int, ...] = (1, 2, 3, 4, 5, 6), tampered: int = 0) -> list[AuditRuntime]:
    """Six real completed audits, optionally with one genuinely tampered."""
    return [audit_of(sub_game, tampered=sub_game == tampered) for sub_game in order]


def empty_audit_of(sub_game: int) -> AuditRuntime:
    """A completed audit for a sub-game that played no turns.

    `TurnCursor` already refuses a sub-game outside 1…6, so an out-of-series
    audit can only exist with no turns at all - which is exactly the shape the
    gate's range guard has to refuse.
    """
    producer = OutboundEvidenceRuntime(
        LocalEvidenceContext(
            evidence.GAME_ID, evidence.GAME_UID, sub_game, evidence.CONFIG, evidence.OURS
        ),
        SecretsNonceSource(),
        CommitmentRecomputer(),
    )
    receiver = AuditRuntime(
        SubGameContext(
            evidence.GAME_ID,
            evidence.GAME_UID,
            sub_game,
            evidence.CONFIG,
            evidence.OURS,
            PEER_GROUP,
        ),
        (),
        CommitmentRecomputer(),
    )
    receiver.accept_final_nonce_reveal(producer.final_nonce_reveal(), PEER_GROUP)
    receiver.accept_audit_disclosure(producer.audit_disclosure())
    return receiver
