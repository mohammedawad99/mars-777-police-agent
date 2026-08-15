"""What a finding is allowed to say, and which findings are tampering."""

import pytest
from semantic_builders import CONFIG, RULES

from mars777_police.app.sealed_record_values import ActorRole
from mars777_police.app.semantic_values import (
    CONSISTENT,
    SCORED_AS_TECHNICAL_LOSS,
    TAMPERING,
    SemanticFinding,
    SemanticVerdict,
)

TAMPERS = (
    SemanticVerdict.WRONG_START,
    SemanticVerdict.BROKEN_TRAJECTORY,
    SemanticVerdict.WRONG_BARRIER_SET,
    SemanticVerdict.DISHONEST_CAPTURE_ANSWER,
)
SCORED = (SemanticVerdict.ILLEGAL_ACTION, SemanticVerdict.FALSE_CAPTURE_CLAIM)


def test_the_consistent_finding_names_no_step_and_no_side() -> None:
    assert CONSISTENT.consistent and CONSISTENT.honest
    assert (CONSISTENT.step, CONSISTENT.at_fault) == (None, None)


def test_a_violation_must_name_the_step_it_happened_at() -> None:
    with pytest.raises(ValueError, match="names its step"):
        SemanticFinding(SemanticVerdict.ILLEGAL_ACTION)


def test_a_consistent_replay_cannot_name_one() -> None:
    with pytest.raises(ValueError, match="names its step"):
        SemanticFinding(SemanticVerdict.CONSISTENT, 3)


@pytest.mark.parametrize("verdict", TAMPERS)
def test_every_falsified_record_is_tampering(verdict: SemanticVerdict) -> None:
    finding = SemanticFinding(verdict, 1, ActorRole.THIEF)
    assert verdict in TAMPERING and verdict not in SCORED_AS_TECHNICAL_LOSS
    assert not finding.honest and not finding.consistent


@pytest.mark.parametrize("verdict", SCORED)
def test_honest_records_of_bad_play_are_scored_not_disqualified(
    verdict: SemanticVerdict,
) -> None:
    """`GAME-003`/`BAR-004` say technical loss and `CRYPTO-005` says score 0 -
    none of them says disqualification, and the record itself is truthful."""
    finding = SemanticFinding(verdict, 2, ActorRole.POLICE)
    assert verdict in SCORED_AS_TECHNICAL_LOSS and verdict not in TAMPERING
    assert finding.honest and not finding.consistent


def test_the_bilateral_verdict_is_both_scored_and_disqualifying() -> None:
    """`CRYPTO-005` scores the declaration; `CRYPTO-004` disqualifies the answer."""
    both = SemanticVerdict.FALSE_CLAIM_AFFIRMED
    assert both in TAMPERING and both in SCORED_AS_TECHNICAL_LOSS
    finding = SemanticFinding(both, 1, ActorRole.THIEF, ActorRole.POLICE)
    assert not finding.honest
    assert (finding.at_fault, finding.also_at_fault) == (ActorRole.THIEF, ActorRole.POLICE)


@pytest.mark.parametrize(
    ("verdict", "also", "expected"),
    [
        (SemanticVerdict.FALSE_CLAIM_AFFIRMED, None, "names a second side"),
        (SemanticVerdict.DISHONEST_CAPTURE_ANSWER, ActorRole.POLICE, "names a second side"),
        (SemanticVerdict.FALSE_CLAIM_AFFIRMED, ActorRole.THIEF, "two different sides"),
    ],
)
def test_a_second_side_is_named_exactly_when_the_verdict_is_bilateral(
    verdict: SemanticVerdict, also: ActorRole | None, expected: str
) -> None:
    with pytest.raises(ValueError, match=expected):
        SemanticFinding(verdict, 1, ActorRole.THIEF, also)


def test_no_unilateral_finding_carries_a_second_side() -> None:
    assert CONSISTENT.also_at_fault is None
    for verdict in (*TAMPERS, *SCORED):
        assert SemanticFinding(verdict, 1, ActorRole.POLICE).also_at_fault is None


def test_the_vocabulary_is_exactly_these_nine() -> None:
    """Eight replay findings, plus the physical-scent verdict JDEC-018 added."""
    assert [verdict.value for verdict in SemanticVerdict] == [
        "CONSISTENT",
        "WRONG_START",
        "BROKEN_TRAJECTORY",
        "ILLEGAL_ACTION",
        "WRONG_BARRIER_SET",
        "FALSE_CAPTURE_CLAIM",
        "DISHONEST_CAPTURE_ANSWER",
        "FALSE_CLAIM_AFFIRMED",
        "DISHONEST_SCENT_EMISSION",
    ]


def test_the_rules_a_replay_runs_on_come_from_the_locked_config() -> None:
    board, terms = RULES.board, CONFIG.board_and_agents
    assert (board.rows, board.cols, board.start_index) == (
        terms.grid_size,
        terms.grid_size,
        terms.axis_start_index,
    )
    assert board.blocked == frozenset()
    assert RULES.quota.max_barriers == CONFIG.movement_and_barriers.max_barriers
    assert (RULES.cop_start, RULES.thief_start) == (terms.cop_start, terms.thief_start)
