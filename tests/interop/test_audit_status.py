"""What a semantic check concluded, and what it is not allowed to imply.

Four outcomes, because three of them are routinely confused. A check that
**passed** and a check that **could not be decided** are different facts, and
collapsing them is how a lawful peer with a leaner payload gets recorded as a
cheat - or, worse, how an undecidable binding question gets recorded as clean.

The truthiness pin below is the one that earns its place. `Optional[bool]`
would have made `if status:` read as "passed", and `NOT_CHECKABLE` would have
silently answered yes to a question nobody could answer.
"""

import pytest

from mars777_police.app.audit_status import CheckProvenance, CheckStatus


def test_the_four_outcomes_are_distinct_values() -> None:
    assert len(set(CheckStatus)) == 4
    assert {s.name for s in CheckStatus} == {
        "VERIFIED",
        "FAILED",
        "NOT_APPLICABLE",
        "NOT_CHECKABLE",
    }


@pytest.mark.parametrize("status", list(CheckStatus))
def test_no_status_can_be_mistaken_for_success_by_truthiness(status: CheckStatus) -> None:
    """`if status:` must never be a way to ask whether a check passed."""
    assert (status is CheckStatus.VERIFIED) == status.passed
    if status is not CheckStatus.VERIFIED:
        assert not status.passed


def test_not_checkable_is_neither_passed_nor_a_violation() -> None:
    """The whole point: undecided is its own answer, not a quiet yes or no."""
    undecided = CheckStatus.NOT_CHECKABLE

    assert not undecided.passed
    assert not undecided.violated
    assert CheckStatus.FAILED.violated
    assert not CheckStatus.VERIFIED.violated


def test_not_applicable_is_not_a_violation_either() -> None:
    assert not CheckStatus.NOT_APPLICABLE.violated
    assert not CheckStatus.NOT_APPLICABLE.passed


def test_the_three_provenances_are_distinct() -> None:
    assert {p.name for p in CheckProvenance} == {
        "SOURCE_BINDING",
        "PROFILE_REQUIRED",
        "PROJECT_ENRICHMENT",
    }
