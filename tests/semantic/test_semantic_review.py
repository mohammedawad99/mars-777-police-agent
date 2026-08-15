"""The whole review, over two real evidence producers and one real audit.

Every disclosure below verifies cryptographically - each is sealed by the real
producer and recomputed by the real `AuditRuntime` - so anything the review
finds is a game that was forged *consistently*, which is precisely the class of
forgery hashes cannot see.
"""

import pytest
import semantic_builders as build
from semantic_builders import COP, MODEL, NORTH, PEER_GROUP, RULES, THIEF, audited, row, seal

from mars777_police.app.audit_values import AuditPhase
from mars777_police.app.capture_values import CaptureAnswer
from mars777_police.app.protocol_errors import LocalDefectError, StaleMessageError
from mars777_police.app.protocol_values import FinalAuditVerdict
from mars777_police.app.sealed_record_values import ActorRole
from mars777_police.app.semantic_review import peer_turns, review_sub_game, sanctioned
from mars777_police.app.semantic_values import CONSISTENT, SemanticFinding, SemanticVerdict
from mars777_police.domain.actions import BarrierAction, MoveAction
from mars777_police.domain.barriers import is_placeable
from mars777_police.domain.board import Position
from mars777_police.domain.rules import Move
from mars777_police.domain.terminal import Outcome

POLICE, THIEF_ROLE = ActorRole.POLICE, ActorRole.THIEF
SOUTH = MoveAction(Move.S)
QUIET = (row(1, CaptureAnswer.NO_QUESTION),)


def sub_game(
    *,
    thief_cell: Position = THIEF,
    claim: Position | None = None,
    answer: CaptureAnswer = CaptureAnswer.NO_QUESTION,
) -> tuple[object, object]:
    """One whole sub-game from the police's side: our turn, theirs, both rows."""
    ours, theirs = build.evidence_for(POLICE), build.evidence_for(THIEF_ROLE)
    seal(ours, 1, COP, SOUTH)
    prepared = seal(theirs, 1, thief_cell, NORTH)
    ours.observe_capture((row(1, answer, claim),))
    audit = audited(build.audit_for(THIEF_ROLE), theirs, [prepared], QUIET)
    return ours, audit


def test_a_legal_sub_game_reviews_as_consistent() -> None:
    ours, audit = sub_game()
    assert audit.verdict is FinalAuditVerdict.VERIFIED_OK
    assert review_sub_game(ours, audit, RULES, MODEL) is CONSISTENT


def test_a_peer_that_opened_off_its_locked_cell_is_caught_after_the_hashes_pass() -> None:
    ours, audit = sub_game(thief_cell=Position(6, 6))
    assert audit.verdict is FinalAuditVerdict.VERIFIED_OK, "the forgery is self-consistent"
    finding = review_sub_game(ours, audit, RULES, MODEL)
    assert finding.verdict is SemanticVerdict.WRONG_START
    assert finding.at_fault is THIEF_ROLE


def test_a_true_claim_denied_by_the_peer_is_a_dishonest_answer() -> None:
    ours, audit = sub_game(claim=THIEF, answer=CaptureAnswer.NOT_CAUGHT)
    finding = review_sub_game(ours, audit, RULES, MODEL)
    assert finding.verdict is SemanticVerdict.DISHONEST_CAPTURE_ANSWER
    assert (finding.step, finding.at_fault) == (1, THIEF_ROLE)


def test_our_own_false_declaration_is_found_by_our_own_review() -> None:
    ours, audit = sub_game(claim=Position(0, 6), answer=CaptureAnswer.NOT_CAUGHT)
    finding = review_sub_game(ours, audit, RULES, MODEL)
    assert finding.verdict is SemanticVerdict.FALSE_CAPTURE_CLAIM
    assert finding.at_fault is POLICE


def test_a_true_claim_confirmed_is_consistent() -> None:
    ours, audit = sub_game(claim=THIEF, answer=CaptureAnswer.CAUGHT)
    assert review_sub_game(ours, audit, RULES, MODEL).consistent


def test_a_review_needs_the_disclosure_it_reviews() -> None:
    ours, _ = sub_game()
    with pytest.raises(LocalDefectError, match="follows the peer's audit disclosure"):
        peer_turns(build.audit_for(THIEF_ROLE))
    assert ours.capture != ()


def test_a_tampering_finding_makes_the_recorded_outcome_tampered() -> None:
    _, audit = sub_game()
    audit.adopt_semantic(SemanticFinding(SemanticVerdict.WRONG_START, 1, THIEF_ROLE))
    assert audit.recorded_outcome.verdict is FinalAuditVerdict.TAMPERED
    assert audit.recorded_outcome.tampered_step == 1
    assert audit.verdict is FinalAuditVerdict.TAMPERED
    assert not audit.verified


def test_a_false_claim_leaves_the_verified_evidence_verified() -> None:
    _, audit = sub_game()
    audit.adopt_semantic(SemanticFinding(SemanticVerdict.FALSE_CAPTURE_CLAIM, 1, POLICE))
    assert audit.verdict is FinalAuditVerdict.VERIFIED_OK
    assert audit.verified


def test_a_finding_arrives_once_and_only_after_the_disclosure() -> None:
    fresh = build.audit_for(THIEF_ROLE)
    assert fresh.phase is AuditPhase.AWAITING_NONCES
    with pytest.raises(StaleMessageError, match="cannot arrive"):
        fresh.adopt_semantic(SemanticFinding(SemanticVerdict.WRONG_START, 1, THIEF_ROLE))
    _, audit = sub_game()
    audit.adopt_semantic(SemanticFinding(SemanticVerdict.WRONG_START, 1, THIEF_ROLE))
    with pytest.raises(StaleMessageError, match="already reviewed"):
        audit.adopt_semantic(SemanticFinding(SemanticVerdict.ILLEGAL_ACTION, 1, THIEF_ROLE))


def test_the_nonce_batch_still_has_to_come_from_the_peer() -> None:
    """The semantic layer adds a check; it removes none of the R7 ones."""
    _, theirs = build.evidence_for(POLICE), build.evidence_for(THIEF_ROLE)
    prepared = seal(theirs, 1, THIEF, NORTH)
    audit = build.audit_for(THIEF_ROLE)
    audit.observe((build.witness(prepared),))
    with pytest.raises(StaleMessageError, match="expected peer"):
        audit.accept_final_nonce_reveal(theirs.final_nonce_reveal(), "SOMEONE-ELSE")
    assert PEER_GROUP != "SOMEONE-ELSE"


def test_an_honestly_committed_illegal_move_is_not_called_tampering() -> None:
    """Every cryptographic fact holds; only the game rule was broken.

    The peer sealed the action it really took, the nonce opens the digest, the
    disclosure matches the sealed material and the transcript is the one we
    observed. What the replay finds is `BAR-004`: placement belongs to the
    police, and the cell it named is one the domain would otherwise accept.
    """
    ours, theirs = build.evidence_for(POLICE), build.evidence_for(THIEF_ROLE)
    seal(ours, 1, COP, SOUTH)
    beside = Position(THIEF.row, THIEF.col + 1)
    prepared = seal(theirs, 1, THIEF, BarrierAction(beside))
    audit = audited(build.audit_for(THIEF_ROLE), theirs, [prepared], QUIET)
    finding = review_sub_game(ours, audit, RULES, MODEL)

    assert is_placeable(RULES.board, THIEF, beside, RULES.quota), "legal but for the role"
    assert finding.verdict is SemanticVerdict.ILLEGAL_ACTION
    assert (finding.step, finding.at_fault) == (1, THIEF_ROLE)
    assert audit.outcome is not None and audit.outcome.verified, "the hashes agreed"
    audit.adopt_semantic(finding)
    assert audit.verdict is FinalAuditVerdict.VERIFIED_OK, "not a hash-mismatch DQ"
    assert audit.verified, "the series is not disqualified by illegal play"
    assert sanctioned(Outcome.SURVIVAL, finding) is Outcome.TECHNICAL_LOSS


def test_a_false_claim_the_peer_confirmed_names_both_sides() -> None:
    """The police declared a cell the thief was not on; the thief said CAUGHT."""
    ours, audit = sub_game(claim=Position(0, 6), answer=CaptureAnswer.CAUGHT)
    finding = review_sub_game(ours, audit, RULES, MODEL)
    assert finding.verdict is SemanticVerdict.FALSE_CLAIM_AFFIRMED
    assert (finding.at_fault, finding.also_at_fault) == (THIEF_ROLE, POLICE)
    audit.adopt_semantic(finding)
    assert audit.verdict is FinalAuditVerdict.TAMPERED, "CRYPTO-004 denies reality"
    assert sanctioned(Outcome.CAPTURE, finding) is Outcome.TECHNICAL_LOSS


def test_a_turn_that_was_sealed_but_never_revealed_asks_nothing() -> None:
    """It is still replayed for legality; it just has no answer to recompute."""
    ours, theirs = build.evidence_for(POLICE), build.evidence_for(THIEF_ROLE)
    seal(ours, 1, COP, SOUTH)
    seal(ours, 2, Position(COP.row + 1, COP.col), SOUTH)
    prepared = seal(theirs, 1, THIEF, NORTH)
    ours.observe_capture((row(1, CaptureAnswer.NO_QUESTION),))
    audit = audited(build.audit_for(THIEF_ROLE), theirs, [prepared], QUIET)
    assert len(ours.ordered) == 2 and len(ours.capture) == 1
    assert review_sub_game(ours, audit, RULES, MODEL).consistent


def test_an_outcome_is_only_recorded_once_the_audit_has_one() -> None:
    with pytest.raises(StaleMessageError, match="has not been audited"):
        _ = build.audit_for(THIEF_ROLE).recorded_outcome


@pytest.mark.parametrize("outcome", list(Outcome))
def test_only_a_false_declaration_changes_the_end_event(outcome: Outcome) -> None:
    assert sanctioned(outcome, CONSISTENT) is outcome
    tampering = SemanticFinding(SemanticVerdict.DISHONEST_CAPTURE_ANSWER, 1, THIEF_ROLE)
    assert sanctioned(outcome, tampering) is outcome
    for scored in (SemanticVerdict.FALSE_CAPTURE_CLAIM, SemanticVerdict.ILLEGAL_ACTION):
        assert sanctioned(outcome, SemanticFinding(scored, 1, POLICE)) is Outcome.TECHNICAL_LOSS
    both = SemanticFinding(SemanticVerdict.FALSE_CLAIM_AFFIRMED, 1, THIEF_ROLE, POLICE)
    assert sanctioned(outcome, both) is Outcome.TECHNICAL_LOSS
