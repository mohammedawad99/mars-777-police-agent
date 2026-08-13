"""The complete scent model two peers must agree on, and what refuses it.

SCENT-003 asks for the **full** emission and decay model plus a concrete numeric
example, verified for identical interpretation. So the model carries its worked
numbers as data, and this proves they are executed against the frozen
recurrence rather than believed.
"""

import dataclasses
from decimal import Decimal

import pytest

from mars777_police.domain.config_model import InvalidScentError, ScentParams
from mars777_police.domain.scent_model import (
    BOUNDED_SATURATING_RADIAL_V1,
    ScentExample,
)
from mars777_police.domain.scent_model_default import (
    DECAY_EXAMPLE,
    FIGURE_4_WEIGHTS,
    SATURATION_EXAMPLE,
    default_kernel,
    default_scent_model,
)
from mars777_police.domain.scent_model_examples import outcome_of, require_truthful_examples


def test_the_default_model_is_the_named_interpretation() -> None:
    model = default_scent_model()
    assert model.model_id == BOUNDED_SATURATING_RADIAL_V1 == "BOUNDED_SATURATING_RADIAL_V1"
    assert (model.center_intensity, model.decay_rate, model.field_size) == (
        Decimal("0.9"),
        Decimal("0.10"),
        5,
    )


def test_the_figure_four_kernel_passes_the_existing_radial_authority() -> None:
    """No second validator: `ScentKernel` is what accepts or refuses it."""
    kernel = default_kernel()
    assert kernel.center == Decimal("0.90")
    assert kernel.weight_at(0, 1) == kernel.weight_at(1, 0) == Decimal("0.62")
    assert kernel.weight_at(1, 1) == Decimal("0.42")
    assert kernel.weight_at(0, 2) == Decimal("0.20")
    assert kernel.weight_at(2, 2) == Decimal("0.04")


def test_every_default_weight_is_decimal_text_never_a_float() -> None:
    assert all(isinstance(weight, str) for row in FIGURE_4_WEIGHTS for weight in row)
    assert all(isinstance(weight, Decimal) for row in default_kernel().weights for weight in row)


def test_the_two_required_examples_are_carried_as_data() -> None:
    model = default_scent_model()
    assert model.examples == (DECAY_EXAMPLE, SATURATION_EXAMPLE)
    assert (DECAY_EXAMPLE.tau_before, DECAY_EXAMPLE.delta, DECAY_EXAMPLE.expected) == (
        Decimal("0.9"),
        Decimal("0"),
        Decimal("0.81"),
    )
    assert SATURATION_EXAMPLE.expected == Decimal("0.9")


def test_both_examples_are_produced_by_the_frozen_recurrence() -> None:
    model = default_scent_model()
    assert outcome_of(DECAY_EXAMPLE, model) == Decimal("0.81"), "(1-0.10)*0.9"
    assert outcome_of(SATURATION_EXAMPLE, model) == Decimal("0.9"), "C-10 saturation"
    assert require_truthful_examples(model) is None


def test_an_example_the_physics_contradicts_is_refused() -> None:
    lying = dataclasses.replace(
        default_scent_model(), examples=(ScentExample(Decimal("0.9"), Decimal(0), Decimal("0.5")),)
    )
    with pytest.raises(InvalidScentError, match=r"claims 0\.5 but the model produces 0\.81"):
        require_truthful_examples(lying)


def test_a_model_names_the_one_interpretation_this_project_offers() -> None:
    with pytest.raises(InvalidScentError, match="model_id must be"):
        dataclasses.replace(default_scent_model(), model_id="RADIAL_V2")


@pytest.mark.parametrize(
    ("field", "value", "expected"),
    [
        ("kernel", "0.9", "kernel must be a ScentKernel"),
        ("params", "params", "params must be ScentParams"),
        ("examples", (), "at least one worked example"),
        ("examples", [DECAY_EXAMPLE], "at least one worked example"),
        ("examples", (DECAY_EXAMPLE, "0.81"), "must be a ScentExample"),
    ],
)
def test_a_malformed_agreement_is_refused(field: str, value: object, expected: str) -> None:
    with pytest.raises(InvalidScentError, match=expected):
        dataclasses.replace(default_scent_model(), **{field: value})


@pytest.mark.parametrize(
    ("field", "value"),
    [("tau_before", Decimal("-0.1")), ("delta", Decimal("-1")), ("expected", Decimal("-0.9"))],
)
def test_an_example_carries_no_negative_number(field: str, value: Decimal) -> None:
    with pytest.raises(InvalidScentError, match=f"example {field} must be >= 0"):
        dataclasses.replace(DECAY_EXAMPLE, **{field: value})


def test_an_example_refuses_a_float() -> None:
    with pytest.raises(InvalidScentError):
        ScentExample(0.9, Decimal(0), Decimal("0.81"))  # type: ignore[arg-type]


def test_the_params_are_the_frozen_appendix_f_values() -> None:
    assert default_scent_model().params == ScentParams()
