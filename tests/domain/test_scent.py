"""Unit tests for the locked scent parameters and the 5x5 emission kernel.

App F Table 16 (all FIXED): centre 0.9, decay 0.10, field 5x5.
The exact 25 kernel weights are NOT locked — Ch 4 p.43 states only a radial
fall-off from the centre — so the domain validates an agreed kernel against the
locked constraints instead of hard-coding Figure-4 values. Values are Decimal
built from strings, never binary floats.
"""

from decimal import Decimal

import pytest

from mars777_police.domain.config_model import (
    FIXED_CENTER_INTENSITY,
    FIXED_DECAY,
    FIXED_FIELD_SIZE,
    InvalidScentError,
    ScentParams,
)

CENTRE_ONLY = (
    ("0", "0", "0", "0", "0"),
    ("0", "0", "0", "0", "0"),
    ("0", "0", "0.9", "0", "0"),
    ("0", "0", "0", "0", "0"),
    ("0", "0", "0", "0", "0"),
)


def test_locked_fixed_parameters() -> None:
    assert Decimal("0.9") == FIXED_CENTER_INTENSITY
    assert Decimal("0.10") == FIXED_DECAY
    assert FIXED_FIELD_SIZE == 5


def test_default_params_match_appendix_f() -> None:
    params = ScentParams()
    assert params.center_intensity == Decimal("0.9")
    assert params.decay == Decimal("0.10")
    assert params.field_size == 5


@pytest.mark.parametrize("value", ["0.8", "1.0", "0.09"])
def test_fixed_centre_deviation_is_rejected(value: str) -> None:
    with pytest.raises(InvalidScentError):
        ScentParams(center_intensity=Decimal(value))


@pytest.mark.parametrize("value", ["0.2", "0.09", "0", "1"])
def test_fixed_decay_deviation_is_rejected(value: str) -> None:
    with pytest.raises(InvalidScentError):
        ScentParams(decay=Decimal(value))


def test_numerically_equal_decay_spelling_is_accepted() -> None:
    # FIXED compares numeric value, so 0.1 and 0.10 are the same locked rate.
    assert ScentParams(decay=Decimal("0.1")).decay == Decimal("0.10")


@pytest.mark.parametrize("value", [3, 4, 6, 7])
def test_fixed_field_size_deviation_is_rejected(value: int) -> None:
    with pytest.raises(InvalidScentError):
        ScentParams(field_size=value)


def test_binary_floats_are_rejected_as_parameters() -> None:
    with pytest.raises(InvalidScentError):
        ScentParams(center_intensity=0.9)  # type: ignore[arg-type]
    with pytest.raises(InvalidScentError):
        ScentParams(decay=0.1)  # type: ignore[arg-type]
