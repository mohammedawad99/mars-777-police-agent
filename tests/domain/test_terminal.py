"""Unit tests for terminal evaluation (outcomes and step semantics).

Ch 3 Table 2 defines exactly three sub-game end events and makes survival
conditional on *no capture*, which is the locked precedence. Configuration
admissibility itself is covered by ``test_terminal_limits.py``.
"""

import pytest

from mars777_police.domain.errors import DomainError
from mars777_police.domain.terminal import (
    InvalidTurnLimitsError,
    Outcome,
    TurnLimits,
    evaluate_terminal,
)

LIMITS = TurnLimits(max_moves=35, survival_threshold=35)


def test_capture_wins_over_every_step_threshold() -> None:
    # Steps stay inside the ceiling: beyond it is invalid input, not an outcome.
    for step in (0, 1, 34, 35):
        assert evaluate_terminal(captured=True, step=step, limits=LIMITS) is Outcome.CAPTURE
    wide = TurnLimits(max_moves=100, survival_threshold=35)
    assert evaluate_terminal(captured=True, step=100, limits=wide) is Outcome.CAPTURE


def test_no_terminal_before_the_survival_threshold() -> None:
    assert evaluate_terminal(captured=False, step=34, limits=LIMITS) is None


def test_survival_fires_exactly_at_the_configured_threshold() -> None:
    assert evaluate_terminal(captured=False, step=35, limits=LIMITS) is Outcome.SURVIVAL


def test_survival_threshold_comes_from_config_not_a_hard_coded_35() -> None:
    limits = TurnLimits(max_moves=60, survival_threshold=40)
    assert evaluate_terminal(captured=False, step=35, limits=limits) is None
    assert evaluate_terminal(captured=False, step=39, limits=limits) is None
    assert evaluate_terminal(captured=False, step=40, limits=limits) is Outcome.SURVIVAL


def test_max_moves_boundary_when_it_is_not_below_the_survival_threshold() -> None:
    limits = TurnLimits(max_moves=40, survival_threshold=35)
    assert evaluate_terminal(captured=False, step=34, limits=limits) is None
    assert evaluate_terminal(captured=False, step=39, limits=limits) is Outcome.SURVIVAL
    assert evaluate_terminal(captured=False, step=40, limits=limits) is Outcome.SURVIVAL


@pytest.mark.parametrize(
    ("max_moves", "survival"),
    [(35, 35), (40, 35), (40, 40), (60, 35), (100, 100)],
)
def test_admissible_threshold_configurations_are_accepted(max_moves: int, survival: int) -> None:
    # JDEC-015: survival_threshold <= max_moves.
    limits = TurnLimits(max_moves=max_moves, survival_threshold=survival)
    assert limits.survival_threshold <= limits.max_moves


@pytest.mark.parametrize(("max_moves", "survival"), [(35, 40), (40, 41), (35, 36), (50, 99)])
def test_unreachable_survival_threshold_is_an_inadmissible_configuration(
    max_moves: int,
    survival: int,
) -> None:
    # JDEC-015: the source defines no outcome for a survival threshold that the
    # step ceiling can never reach, so the configuration is refused instead.
    with pytest.raises(InvalidTurnLimitsError):
        TurnLimits(max_moves=max_moves, survival_threshold=survival)


def test_step_beyond_the_ceiling_is_invalid_input_not_an_outcome() -> None:
    limits = TurnLimits(max_moves=35, survival_threshold=35)
    with pytest.raises(InvalidTurnLimitsError):
        evaluate_terminal(captured=False, step=36, limits=limits)
    with pytest.raises(InvalidTurnLimitsError):
        evaluate_terminal(captured=True, step=36, limits=limits)


def test_step_at_the_ceiling_follows_the_configured_thresholds() -> None:
    assert evaluate_terminal(captured=False, step=40, limits=TurnLimits(40, 35)) is Outcome.SURVIVAL
    assert evaluate_terminal(captured=False, step=40, limits=TurnLimits(40, 40)) is Outcome.SURVIVAL
    assert evaluate_terminal(captured=False, step=39, limits=TurnLimits(40, 40)) is None


def test_no_unspecified_terminal_error_remains() -> None:
    from mars777_police.domain import terminal

    assert not hasattr(terminal, "UnspecifiedTerminalError")
    from mars777_police import domain

    assert "UnspecifiedTerminalError" not in domain.__all__


def test_evaluation_is_deterministic_and_order_free() -> None:
    limits = TurnLimits(max_moves=35, survival_threshold=35)
    for _ in range(5):
        assert evaluate_terminal(captured=False, step=35, limits=limits) is Outcome.SURVIVAL
        assert evaluate_terminal(captured=True, step=35, limits=limits) is Outcome.CAPTURE


def test_negative_or_malformed_step_is_rejected() -> None:
    with pytest.raises(InvalidTurnLimitsError):
        evaluate_terminal(captured=False, step=-1, limits=LIMITS)
    with pytest.raises(InvalidTurnLimitsError):
        evaluate_terminal(captured=False, step="35", limits=LIMITS)  # type: ignore[arg-type]


def test_terminal_errors_are_domain_errors() -> None:
    assert issubclass(InvalidTurnLimitsError, DomainError)


def test_technical_loss_is_not_detected_by_the_domain() -> None:
    # Crash / timeout / cryptographic forgery are protocol-layer facts; the
    # domain only owns the scoring key for them.
    from mars777_police.domain import terminal

    assert not any(name.startswith("is_technical") for name in dir(terminal))


def test_no_tie_or_extra_outcome_was_introduced() -> None:
    assert len(list(Outcome)) == 3
    assert "TIE" not in {o.name for o in Outcome}
    assert Outcome.TECHNICAL_LOSS.value == "TECHNICAL_LOSS"


def test_capture_beats_survival_at_the_same_step() -> None:
    limits = TurnLimits(max_moves=35, survival_threshold=35)
    assert evaluate_terminal(captured=True, step=35, limits=limits) is Outcome.CAPTURE
    assert evaluate_terminal(captured=False, step=35, limits=limits) is Outcome.SURVIVAL
