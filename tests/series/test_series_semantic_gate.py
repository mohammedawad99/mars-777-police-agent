"""What the series gate does with a replay's finding.

The gate has always recorded one outcome per sub-game. What it records now is
the hashes *and* the replay, which splits the two failures apart: a forged game
blocks the series exactly as a failed digest does, while a wrong declaration
leaves a verified series verified and is paid for in points instead.
"""

import pytest
import series_builders as build

from mars777_police.app.protocol_values import FinalAuditVerdict
from mars777_police.app.sealed_record_values import ActorRole
from mars777_police.app.semantic_values import SemanticFinding, SemanticVerdict
from mars777_police.app.series_audit_gate import SeriesAuditGate

DISHONEST = SemanticFinding(SemanticVerdict.DISHONEST_CAPTURE_ANSWER, 1, ActorRole.THIEF)
FALSE_CLAIM = SemanticFinding(SemanticVerdict.FALSE_CAPTURE_CLAIM, 1, ActorRole.POLICE)
ILLEGAL = SemanticFinding(SemanticVerdict.ILLEGAL_ACTION, 1, ActorRole.THIEF)
BOTH = SemanticFinding(SemanticVerdict.FALSE_CLAIM_AFFIRMED, 1, ActorRole.THIEF, ActorRole.POLICE)


def gate_over(finding: SemanticFinding | None = None, sub_game: int = 2) -> SeriesAuditGate:
    """Six real completed audits, with *finding* adopted by one of them."""
    gate = SeriesAuditGate()
    for audit in build.series():
        if finding is not None and audit.context.sub_game == sub_game:
            audit.adopt_semantic(finding)
        gate.record(audit)
    return gate


def test_six_clean_sub_games_still_add_up_to_a_verified_series() -> None:
    gate = gate_over()
    assert gate.complete
    assert gate.verdict is FinalAuditVerdict.VERIFIED_OK


def test_one_dishonest_answer_blocks_the_whole_series() -> None:
    gate = gate_over(DISHONEST)
    assert gate.verdict is FinalAuditVerdict.TAMPERED
    assert gate.outcomes[2].tampered_step == 1
    assert all(gate.outcomes[other].verified for other in (1, 3, 4, 5, 6))


def test_a_verified_series_survives_a_false_declaration() -> None:
    """The sub-game is lost 0/0; the evidence it produced was never in doubt."""
    gate = gate_over(FALSE_CLAIM)
    assert gate.verdict is FinalAuditVerdict.VERIFIED_OK
    assert gate.outcomes[2].verified


def test_an_illegal_action_is_scored_rather_than_disqualifying() -> None:
    """`GAME-003`/`BAR-004` sanction bad play; the evidence itself was honest."""
    gate = gate_over(ILLEGAL)
    assert gate.verdict is FinalAuditVerdict.VERIFIED_OK
    assert gate.outcomes[2].verified


def test_a_false_claim_the_peer_confirmed_still_blocks_the_series() -> None:
    gate = gate_over(BOTH)
    assert gate.verdict is FinalAuditVerdict.TAMPERED
    assert gate.outcomes[2].tampered_step == 1


@pytest.mark.parametrize("verdict", sorted(SemanticVerdict))
def test_every_verdict_records_exactly_what_the_replay_decided(verdict: SemanticVerdict) -> None:
    finding = _finding_for(verdict)
    gate = gate_over(finding)
    blocked = gate.verdict is FinalAuditVerdict.TAMPERED
    assert blocked is not finding.honest


def _finding_for(verdict: SemanticVerdict) -> SemanticFinding:
    """One finding of each verdict, each with the sides that verdict allows."""
    if verdict is SemanticVerdict.CONSISTENT:
        return SemanticFinding(verdict)
    if verdict is SemanticVerdict.FALSE_CLAIM_AFFIRMED:
        return SemanticFinding(verdict, 1, ActorRole.THIEF, ActorRole.POLICE)
    return SemanticFinding(verdict, 1, ActorRole.THIEF)


def test_a_hash_failure_is_still_a_hash_failure() -> None:
    """The semantic layer adds a way to fail, and removes none."""
    gate = SeriesAuditGate()
    for audit in build.series(tampered=3):
        gate.record(audit)
    assert gate.verdict is FinalAuditVerdict.TAMPERED
    assert gate.outcomes[3].tampered_step == 1
