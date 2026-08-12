"""The official log: acknowledgement events, ordering, and the audit annotations.

The pairs here are real - a production `OutboundEvidenceRuntime` disclosing to a
production `AuditRuntime` over production crypto - so a rendered log is the log a
real sub-game would leave, not a hand-built dictionary.
"""

import evidence_builders as ev
import pytest

from mars777_police.app.audit_runtime import AuditRuntime
from mars777_police.app.log_document import finalized_log
from mars777_police.app.log_events import ACK, COMMIT, REVEAL
from mars777_police.app.outbound_evidence_runtime import OutboundEvidenceRuntime
from mars777_police.app.protocol_errors import LocalDefectError
from mars777_police.app.protocol_values import FinalAuditVerdict, Sha256Digest
from mars777_police.app.sealed_record_values import ActorRole, Intent, SealedState
from mars777_police.app.turn_cursor import TurnCursor
from mars777_police.app.turn_protocol_state import AckEvidence
from mars777_police.domain.actions import MoveAction
from mars777_police.domain.rules import Move

STEPS = (1, 2)
OURS, PEER = ActorRole.POLICE, ActorRole.THIEF


def own_producer() -> OutboundEvidenceRuntime:
    """Our own side's evidence owner - the police half of the same sub-game."""
    from mars777_police.app.outbound_evidence_values import LocalEvidenceContext
    from mars777_police.protocol.audit_commitment import CommitmentRecomputer
    from mars777_police.protocol.secure_nonce import SecretsNonceSource

    context = LocalEvidenceContext(ev.GAME_ID, ev.GAME_UID, ev.SUB_GAME, ev.CONFIG, OURS)
    runtime = OutboundEvidenceRuntime(context, SecretsNonceSource(), CommitmentRecomputer())
    for step in STEPS:
        runtime.prepare_turn(
            state=SealedState(ev.CONFIG, ev.POS[step], (), step, OURS),
            action=MoveAction(Move.N),
            intent=Intent.TRUTH,
            hint=ev.HINTS[step],
            cursor=TurnCursor(ev.SUB_GAME, step),
        )
    return runtime


def audited(tamper: bool = False) -> tuple[OutboundEvidenceRuntime, AuditRuntime]:
    """A real disclosed sub-game: our police half, and the audited thief half."""
    producer = ev.producer()
    prepared = [ev.prepare(producer, step) for step in STEPS]
    receiver = ev.receiver(prepared, STEPS)
    receiver.accept_final_nonce_reveal(producer.final_nonce_reveal(), ev.PEER_GROUP)
    document = producer.audit_disclosure()
    if tamper:
        entries = document["entries"]
        assert isinstance(entries, list)
        entries[0]["hint"] = "a hint that was never sent"
    receiver.accept_audit_disclosure(document)
    return own_producer(), receiver


def acked(receiver: AuditRuntime, step: int, by_role: ActorRole) -> None:
    """Adopt one acknowledgement exactly as a finished turn would hand it over."""
    cursor = TurnCursor(ev.SUB_GAME, step)
    digest = Sha256Digest(f"{step}" * 64)
    receiver.acks += (AckEvidence(cursor, digest, by_role),)


def phases(document: object, step: int) -> list[str]:
    """The event phases recorded for one step, in the order they were written."""
    entries = document["entries"]  # type: ignore[index]
    assert isinstance(entries, list)
    return [
        str(entry.get("phase"))
        for entry in entries
        if step in (entry.get("step"), entry.get("ack_of_step"))
    ]


def test_a_turn_is_written_as_commit_then_ack_then_reveal() -> None:
    producer, receiver = audited()
    acked(receiver, 1, PEER)
    document = finalized_log(producer, receiver)
    assert phases(document, 1)[:3] == [COMMIT, ACK, REVEAL]


def test_the_ack_event_carries_the_acknowledged_step_digest_and_acking_role() -> None:
    producer, receiver = audited()
    cursor = TurnCursor(ev.SUB_GAME, 2)
    digest = Sha256Digest("b" * 64)
    receiver.acks += (AckEvidence(cursor, digest, PEER),)
    entries = finalized_log(producer, receiver)["entries"]
    assert isinstance(entries, list)
    ack = next(entry for entry in entries if entry["phase"] == ACK)
    assert ack["ack_of_step"] == 2
    assert ack["ack_commit"] == digest.value
    assert ack["by_role"] == PEER.value
    assert ack["sub_game"] == ev.SUB_GAME
    assert "step" not in ack


def test_an_unacknowledged_commitment_writes_no_ack_event() -> None:
    producer, receiver = audited()
    entries = finalized_log(producer, receiver)["entries"]
    assert isinstance(entries, list)
    assert [entry for entry in entries if entry["phase"] == ACK] == []


def test_the_verdict_and_annotations_are_ours_and_only_where_measured() -> None:
    producer, receiver = audited(tamper=True)
    document = finalized_log(producer, receiver)
    audit = document["audit"]
    assert isinstance(audit, dict)
    assert audit["result"] == FinalAuditVerdict.TAMPERED.value
    assert audit["tampered_step"] == 1
    entries = document["entries"]
    assert isinstance(entries, list)
    commits = [entry for entry in entries if entry["phase"] == COMMIT]
    verified = {entry["step"]: entry["verified"] for entry in commits if "verified" in entry}
    assert verified == {1: False, 2: None}


def test_a_verified_sub_game_annotates_every_disclosed_turn() -> None:
    producer, receiver = audited()
    document = finalized_log(producer, receiver)
    audit = document["audit"]
    assert isinstance(audit, dict)
    assert (audit["result"], audit["tampered_step"]) == (FinalAuditVerdict.VERIFIED_OK.value, None)
    assert len(audit["final_reveal"]) == 2 * len(STEPS)  # type: ignore[arg-type]


def test_a_log_needs_an_audit_that_actually_completed() -> None:
    producer = ev.producer()
    ev.prepare(producer, 1)
    with pytest.raises(LocalDefectError, match="was audited"):
        finalized_log(producer, ev.receiver([], ()))


def test_a_log_refuses_evidence_from_another_sub_game() -> None:
    producer, receiver = audited()
    from mars777_police.app.outbound_evidence_values import LocalEvidenceContext
    from mars777_police.protocol.audit_commitment import CommitmentRecomputer
    from mars777_police.protocol.secure_nonce import SecretsNonceSource

    context = LocalEvidenceContext(ev.GAME_ID, ev.GAME_UID, ev.SUB_GAME + 1, ev.CONFIG, OURS)
    other = OutboundEvidenceRuntime(context, SecretsNonceSource(), CommitmentRecomputer())
    with pytest.raises(LocalDefectError, match="different sub-games"):
        finalized_log(other, receiver)
    assert producer.context.sub_game == ev.SUB_GAME
