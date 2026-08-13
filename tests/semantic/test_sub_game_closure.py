"""Closing a sub-game: review first, sanction next, log last.

The log written here is the official `log_<game_id>_gNN.json` body, so what the
review concluded has to be *in* it - both directions of the capture transcript
and the finding itself - rather than only in the runtime that decided it.
"""

import pytest
import semantic_builders as build
from semantic_builders import CONFIG, COP, NORTH, THIEF, audited, row, seal
from test_semantic_review import QUIET, SOUTH

from mars777_police.app.capture_values import CaptureAnswer
from mars777_police.app.protocol_errors import LocalDefectError
from mars777_police.app.protocol_values import FinalAuditVerdict
from mars777_police.app.sealed_record_values import ActorRole
from mars777_police.app.semantic_values import SemanticVerdict
from mars777_police.app.sub_game_closure import closed_sub_game
from mars777_police.domain.actions import BarrierAction
from mars777_police.domain.board import Position
from mars777_police.domain.scoring import ScoreLine, score_for
from mars777_police.domain.terminal import Outcome

POLICE, THIEF_ROLE = ActorRole.POLICE, ActorRole.THIEF


def closed(
    claim: Position | None = None,
    answer: CaptureAnswer = CaptureAnswer.NO_QUESTION,
    outcome: Outcome = Outcome.CAPTURE,
) -> object:
    """One real sub-game, closed through the production closure."""
    ours, theirs = build.evidence_for(POLICE), build.evidence_for(THIEF_ROLE)
    seal(ours, 1, COP, SOUTH)
    prepared = seal(theirs, 1, THIEF, NORTH)
    ours.observe_capture((row(1, answer, claim),))
    audit = audited(build.audit_for(THIEF_ROLE), theirs, [prepared], QUIET)
    return closed_sub_game(ours, audit, CONFIG, outcome)


def reveals(document: object) -> list[dict[str, object]]:
    """Every reveal event of the finalized log, in the order it was written."""
    entries = document["entries"]  # type: ignore[index]
    return [entry for entry in entries if entry["phase"] == "reveal"]


def test_a_clean_sub_game_keeps_the_end_event_that_was_played() -> None:
    result = closed()
    assert result.outcome is Outcome.CAPTURE
    assert result.finding.consistent
    assert result.document["audit"]["result"] == FinalAuditVerdict.VERIFIED_OK.value


def test_the_log_carries_the_finding_the_replay_reached() -> None:
    semantic = closed().document["audit"]["semantic"]
    assert semantic == {
        "verdict": "CONSISTENT",
        "step": None,
        "at_fault": None,
        "also_at_fault": None,
    }


def test_both_directions_of_the_transcript_reach_the_official_log() -> None:
    ours, theirs = reveals(closed(claim=THIEF, answer=CaptureAnswer.CAUGHT).document)
    assert (ours["role"], ours["capture_claim"], ours["capture_answer"]) == (
        POLICE.value,
        [THIEF.row, THIEF.col],
        "CAUGHT",
    )
    assert (theirs["role"], theirs["capture_claim"], theirs["capture_answer"]) == (
        THIEF_ROLE.value,
        None,
        "NO_QUESTION",
    )


def test_a_false_declaration_ends_the_sub_game_as_a_technical_loss() -> None:
    result = closed(claim=Position(0, 6), answer=CaptureAnswer.NOT_CAUGHT)
    assert result.finding.verdict is SemanticVerdict.FALSE_CAPTURE_CLAIM
    assert result.outcome is Outcome.TECHNICAL_LOSS
    assert result.document["audit"]["result"] == FinalAuditVerdict.VERIFIED_OK.value
    assert result.document["audit"]["semantic"]["at_fault"] == POLICE.value


def test_a_dishonest_answer_makes_the_written_log_say_tampered() -> None:
    result = closed(claim=THIEF, answer=CaptureAnswer.NOT_CAUGHT)
    audit = result.document["audit"]
    assert result.finding.verdict is SemanticVerdict.DISHONEST_CAPTURE_ANSWER
    assert (audit["result"], audit["tampered_step"]) == (FinalAuditVerdict.TAMPERED.value, 1)
    assert audit["semantic"]["at_fault"] == THIEF_ROLE.value
    assert result.outcome is Outcome.CAPTURE, "tampering is blocked, not scored"


def test_a_false_claim_the_peer_confirmed_is_written_with_both_faults() -> None:
    """It is not a capture: the sub-game is scored 0/0 *and* the series blocks."""
    result = closed(claim=Position(6, 6), answer=CaptureAnswer.CAUGHT)
    audit = result.document["audit"]
    assert result.finding.verdict is SemanticVerdict.FALSE_CLAIM_AFFIRMED
    assert audit["semantic"] == {
        "verdict": "FALSE_CLAIM_AFFIRMED",
        "step": 1,
        "at_fault": THIEF_ROLE.value,
        "also_at_fault": POLICE.value,
    }
    assert (audit["result"], audit["tampered_step"]) == (FinalAuditVerdict.TAMPERED.value, 1)
    assert result.outcome is Outcome.TECHNICAL_LOSS
    assert score_for(result.outcome) == ScoreLine(cop=0, thief=0)


def test_an_illegal_disclosed_move_is_scored_and_leaves_the_evidence_verified() -> None:
    ours, theirs = build.evidence_for(POLICE), build.evidence_for(THIEF_ROLE)
    seal(ours, 1, COP, SOUTH)
    prepared = seal(theirs, 1, THIEF, BarrierAction(Position(THIEF.row, THIEF.col + 1)))
    audit = audited(build.audit_for(THIEF_ROLE), theirs, [prepared], QUIET)
    result = closed_sub_game(ours, audit, CONFIG, Outcome.SURVIVAL)
    written = result.document["audit"]
    assert result.finding.verdict is SemanticVerdict.ILLEGAL_ACTION
    assert result.outcome is Outcome.TECHNICAL_LOSS
    assert score_for(result.outcome) == ScoreLine(cop=0, thief=0)
    assert written["result"] == FinalAuditVerdict.VERIFIED_OK.value
    assert written["tampered_step"] is None
    assert written["semantic"]["at_fault"] == THIEF_ROLE.value


def test_a_sub_game_cannot_be_closed_without_the_config_it_was_played_under() -> None:
    ours, theirs = build.evidence_for(POLICE), build.evidence_for(THIEF_ROLE)
    seal(ours, 1, COP, SOUTH)
    prepared = seal(theirs, 1, THIEF, NORTH)
    audit = audited(build.audit_for(THIEF_ROLE), theirs, [prepared], QUIET)
    with pytest.raises(LocalDefectError, match="config this series locked"):
        closed_sub_game(ours, audit, None, Outcome.CAPTURE)


def test_the_review_runs_before_the_log_is_rendered() -> None:
    """A log rendered first would carry the verdict that was still being decided."""
    ours, theirs = build.evidence_for(POLICE), build.evidence_for(THIEF_ROLE)
    seal(ours, 1, COP, SOUTH)
    prepared = seal(theirs, 1, Position(6, 6), NORTH)
    audit = audited(build.audit_for(THIEF_ROLE), theirs, [prepared], QUIET)
    assert audit.outcome is not None and audit.outcome.verified, "the hashes agreed"
    result = closed_sub_game(ours, audit, CONFIG, Outcome.CAPTURE)
    written = result.document["audit"]
    assert written["result"] == FinalAuditVerdict.TAMPERED.value
    assert written["semantic"]["verdict"] == SemanticVerdict.WRONG_START.value
    assert written["tampered_step"] == 1
