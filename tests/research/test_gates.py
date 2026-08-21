"""The promotion gates, applied exactly as they were frozen.

These are the rules that decide whether a candidate survives, so they are tested
against the boundary rather than against a comfortable example: a drop of
exactly the threshold, an interval that just touches zero, a cell too small to
carry an interval at all.
"""

import pytest
from research.gates import (
    ADVANCED,
    MATERIAL_DROP,
    NOT_ADVANCED,
    REJECTED_GATE,
    Cell,
    material_regression,
    overall_passes,
    verdict_for,
)


def cell(delta: float, low: float | None, high: float | None, n: int = 300) -> Cell:
    return Cell(group="evasive", n=n, delta=delta, low=low, high=high)


def test_the_material_threshold_is_the_one_frozen_before_any_candidate_ran() -> None:
    assert MATERIAL_DROP == 0.05


def test_a_drop_bigger_than_the_threshold_with_a_negative_interval_is_material() -> None:
    assert material_regression(cell(-0.08, -0.12, -0.03)) is True


def test_a_drop_bigger_than_the_threshold_whose_interval_touches_zero_is_not() -> None:
    """Inside the interval it is noise, however large the point estimate looks."""
    assert material_regression(cell(-0.08, -0.15, 0.01)) is False


def test_a_drop_at_exactly_the_threshold_is_not_material() -> None:
    """The rule says *more than* five points, and a boundary must not drift."""
    assert material_regression(cell(-MATERIAL_DROP, -0.09, -0.01)) is False


def test_a_small_drop_with_a_clearly_negative_interval_is_still_not_material() -> None:
    """Confidently small is not the same as materially bad."""
    assert material_regression(cell(-0.0156, -0.03, -0.002)) is False


def test_a_cell_with_no_interval_cannot_be_declared_a_material_regression() -> None:
    """Below the bootstrap minimum there is no evidence to convict on."""
    assert material_regression(cell(-0.30, None, None, n=3)) is False


def test_a_gain_is_never_a_regression() -> None:
    assert material_regression(cell(0.20, 0.10, 0.30)) is False


def test_the_overall_rule_needs_both_a_positive_delta_and_a_positive_lower_bound() -> None:
    assert overall_passes(cell(0.06, 0.046, 0.075)) is True
    assert overall_passes(cell(0.06, -0.001, 0.12)) is False
    assert overall_passes(cell(-0.01, -0.05, 0.03)) is False
    assert overall_passes(cell(0.06, None, None)) is False


def test_a_candidate_that_wins_but_is_not_selected_is_not_recorded_as_failing() -> None:
    """C2's status: it beat the baseline and lost the selection to C4.

    The 9B-1A screening table collapsed both into one word, which reads as
    "C2 failed" - it did not.
    """
    assert verdict_for(passed_gates=True, selected=True) == ADVANCED
    assert verdict_for(passed_gates=True, selected=False) == NOT_ADVANCED
    assert verdict_for(passed_gates=False, selected=False) == REJECTED_GATE


def test_a_candidate_cannot_be_selected_while_failing_a_gate() -> None:
    with pytest.raises(ValueError, match="cannot be selected"):
        verdict_for(passed_gates=False, selected=True)


def test_the_three_statuses_are_distinct_words() -> None:
    assert len({ADVANCED, NOT_ADVANCED, REJECTED_GATE}) == 3
