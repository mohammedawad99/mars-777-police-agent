"""Unit tests for terminal / survival evaluation.

GAME-008 and PRD01-FR-060/061: the step ceiling and the survival threshold are
read from configuration (App F T15 #3/#4, both MINIMUM 35) and never hard-coded.
Ch 3 Table 2 defines exactly three sub-game end events — capture, prolonged
survival, technical loss — and makes survival conditional on *no capture*, which
is the locked precedence used here.
"""

import dataclasses

import pytest

from mars777_police.domain.terminal import (
    MIN_MAX_MOVES,
    MIN_SURVIVAL_THRESHOLD,
    InvalidTurnLimitsError,
    Outcome,
    TurnLimits,
)

LIMITS = TurnLimits(max_moves=35, survival_threshold=35)


def test_locked_minimums() -> None:
    assert MIN_MAX_MOVES == 35
    assert MIN_SURVIVAL_THRESHOLD == 35


@pytest.mark.parametrize("value", [34, 0, -1])
def test_limits_below_the_locked_floor_are_rejected(value: int) -> None:
    with pytest.raises(InvalidTurnLimitsError):
        TurnLimits(max_moves=value, survival_threshold=35)
    with pytest.raises(InvalidTurnLimitsError):
        TurnLimits(max_moves=35, survival_threshold=value)


@pytest.mark.parametrize("value", ["35", 35.0, None, True])
def test_malformed_limits_are_rejected(value: object) -> None:
    with pytest.raises(InvalidTurnLimitsError):
        TurnLimits(max_moves=value, survival_threshold=35)  # type: ignore[arg-type]


def test_raised_limits_are_accepted() -> None:
    limits = TurnLimits(max_moves=50, survival_threshold=40)
    assert (limits.max_moves, limits.survival_threshold) == (50, 40)


def test_limits_are_immutable() -> None:
    with pytest.raises(dataclasses.FrozenInstanceError):
        LIMITS.max_moves = 99  # type: ignore[misc]


def test_outcome_vocabulary_has_no_sub_game_tie() -> None:
    # Ch 3 Table 2 has no tie row; tie is a series/opponent aggregate (App F T17 #5).
    assert {o.value for o in Outcome} == {"CAPTURE", "SURVIVAL", "TECHNICAL_LOSS"}
