"""The finalized per-sub-game log: what was played, and what we concluded.

`LOG_CONTRACT.md` freezes one log model in two states. *DISCLOSURE-READY* is what
`submit_audit` carries and `audit_disclosure_writer` already renders. This builds
the *AUDITED-LOCAL* state: the same entries, plus the nonces the final audit
released and the verdict **we** computed. No second schema exists - the shared
core is reused field for field, and only the local-derived annotations are added.

**Both sides appear, each from its own evidence.** Our turns come from the
records `OutboundEvidenceRuntime` sealed and the emissions it retained; the
peer's come from the disclosure it sent and the turns we witnessed live. Every
audited commitment therefore arrives with its eight sealed members and its nonce,
exactly what a replayer needs to recompute `H_commit` and compare.

**`verified` is only ever claimed where it was measured.** `AuditRuntime` stops
at the first step that fails, so steps after it read `null` rather than a guess;
our own turns read `null` too, because the peer - not us - audits them. A peer's
claim about `audit.result` is never accepted as evidence.

Acknowledgements are events of their own, in protocol order: commit, then the
acknowledgement of that commitment, then the reveal. `by_role` is attribution
this side derived from the config-locked roles - never a transmitted field."""

from ..domain.scent_emission import ScentEmission
from .audit_disclosure import turns
from .audit_disclosure_writer import AuditDocument
from .audit_runtime import AuditRuntime
from .capture_transcript import CaptureRecord
from .log_events import (
    ack_event,
    final_reveal,
    own_commit,
    own_reveal,
    peer_commit,
    peer_reveal,
    verified_at,
)
from .outbound_evidence_runtime import OutboundEvidenceRuntime
from .protocol_errors import LocalDefectError
from .scent_records import ScentRecord
from .sealed_record_values import ActorRole
from .semantic_values import SemanticFinding
from .turn_protocol_state import AckEvidence


def _acked(ack: AckEvidence | None, sub_game: int) -> list[dict[str, object]]:
    """The one ack event for a commitment, or none if it was never acknowledged."""
    return [] if ack is None else [ack_event(ack, sub_game)]


def _side(role: ActorRole | None) -> str | None:
    """One named side of a finding, or `null` where the replay names none."""
    return None if role is None else role.value


def semantic_value(finding: SemanticFinding) -> dict[str, object]:
    """The replay's finding, in the four fields the audit block records it as.

    `also_at_fault` is written on every finding - `null` for the unilateral ones -
    so a reader never has to decide whether an absent key means "nobody else" or
    "an older writer"."""
    return {
        "verdict": finding.verdict.value,
        "step": finding.step,
        "at_fault": _side(finding.at_fault),
        "also_at_fault": _side(finding.also_at_fault),
    }


def _rows(capture: tuple[CaptureRecord, ...]) -> dict[int, CaptureRecord]:
    """One direction's capture transcript, addressed by the step it belongs to."""
    return {row.cursor.step: row for row in capture}


def _scent(history: tuple[ScentRecord, ...]) -> dict[int, ScentRecord]:
    """One direction's scent history, addressed by the step it belongs to.

    Bound by cursor, never by position in a list: a reveal must receive its own
    emission or none. Two rows for one step would make that ambiguous, so it is
    refused rather than resolved to whichever arrived last."""
    rows = {row.cursor.step: row for row in history}
    if len(rows) != len(history):
        raise LocalDefectError("a retained scent history names one step twice")
    return rows


def _emission(
    history: dict[int, ScentRecord], step: int, revealed: bool, counted: bool
) -> ScentEmission | None:
    """The emission that reveal really carried, or `None` where it carried none.

    *counted* says this sub-game was played under the scent-carrying contract,
    which the retained histories themselves establish: a session that negotiated
    it emitted on every reveal, one that did not emitted nowhere. Under it a
    reveal that completed - the signal the capture row already uses - must still
    have its history, so the log is refused rather than holed."""
    found = history.get(step)
    if found is None and revealed and counted:
        raise LocalDefectError(f"step {step} completed a counted reveal with no retained scent")
    return None if found is None else found.emission


def finalized_log(evidence: OutboundEvidenceRuntime, audit: AuditRuntime) -> AuditDocument:
    """Render the audited local log for one completed, audited sub-game."""
    disclosure = audit.disclosure
    outcome = None if audit.outcome is None else audit.recorded_outcome
    if outcome is None or disclosure is None:
        raise LocalDefectError("a log is finalized only after this sub-game was audited")
    context = evidence.context
    if (context.game_id, context.game_uid, context.sub_game) != (
        audit.context.game_id,
        audit.context.game_uid,
        audit.context.sub_game,
    ):
        raise LocalDefectError("the evidence and the audit describe different sub-games")
    records, disclosed = evidence.ordered, turns(disclosure)
    ours = {record.cursor.step: record for record in records}
    theirs = {turn.step: turn for turn in disclosed}
    acks = {(ack.cursor.step, ack.by_role): ack for ack in audit.acks}
    asked, answered = _rows(evidence.capture), _rows(audit.capture)
    sent, received = _scent(evidence.scent), _scent(audit.expected_scent)
    counted = bool(sent) or bool(received)
    role, peer_role = context.role, audit.context.peer_role
    entries: list[dict[str, object]] = []
    for step in sorted(set(ours) | set(theirs)):
        record = ours.get(step)
        if record is not None:
            entries.append(own_commit(record, role))
            entries += _acked(acks.get((step, peer_role)), context.sub_game)
            ours_at = _emission(sent, step, asked.get(step) is not None, counted)
            entries.append(own_reveal(record, role, asked.get(step), ours_at))
        turn = theirs.get(step)
        if turn is not None:
            entries.append(peer_commit(turn, verified_at(step, outcome.tampered_step)))
            entries += _acked(acks.get((step, role)), context.sub_game)
            theirs_at = _emission(received, step, answered.get(step) is not None, counted)
            entries.append(peer_reveal(turn, answered.get(step), theirs_at))
    return {
        "game_id": context.game_id,
        "game_uid": context.game_uid,
        "sub_game": context.sub_game,
        "config_sha256": context.config_sha256.value,
        "entries": entries,
        "audit": {
            "final_reveal": final_reveal(records, context.role, audit),
            "result": outcome.verdict.value,
            "tampered_step": outcome.tampered_step,
            "semantic": semantic_value(audit.semantic),
        },
    }
