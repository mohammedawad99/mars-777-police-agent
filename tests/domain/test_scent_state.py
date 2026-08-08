"""Scent state-domain invariant and the saturating update (conflict C-10).

Ch 4 §4.3 defines tau_ij(t) as a continuous value in **[0, 0.9]** while writing
the update with only a lower clamp. C-10 resolves that contradiction in favour
of the explicit state domain, so the implemented recurrence saturates:

    tau_next = min(0.9, max(0, (1 - rho) * tau_current + delta_tau))

Saturation is a boundary operation only: a raw result below 0.9 stays exactly
additive.
"""

from decimal import Decimal

import pytest

from mars777_police.domain.board import Board, Position
from mars777_police.domain.config_model import InvalidScentError, ScentParams
from mars777_police.domain.scent import MAX_SCENT_STATE, ScentField
from mars777_police.domain.scent_kernel import ScentKernel

GRID = 7
CENTRE = Position(3, 3)
PARAMS = ScentParams()
BOARD = Board(rows=GRID, cols=GRID)

CENTRE_ONLY = ScentKernel.from_rows(
    tuple(tuple("0.9" if (r, c) == (2, 2) else "0" for c in range(5)) for r in range(5)),
)
HALF_KERNEL = ScentKernel.from_rows(
    tuple(tuple("0.9" if (r, c) == (2, 2) else "0.2" for c in range(5)) for r in range(5)),
)


def _grid(value: object) -> tuple[tuple[object, ...], ...]:
    return tuple(tuple(value for _ in range(GRID)) for _ in range(GRID))


def test_the_state_bound_is_the_source_domain() -> None:
    assert Decimal("0.9") == MAX_SCENT_STATE


def test_field_rejects_a_cell_below_zero() -> None:
    with pytest.raises(InvalidScentError):
        ScentField(GRID, GRID, 0, _grid(Decimal("-0.01")))  # type: ignore[arg-type]


def test_field_rejects_a_cell_above_the_state_bound() -> None:
    with pytest.raises(InvalidScentError):
        ScentField(GRID, GRID, 0, _grid(Decimal("0.91")))  # type: ignore[arg-type]
    with pytest.raises(InvalidScentError):
        ScentField(GRID, GRID, 0, _grid(Decimal("1.71")))  # type: ignore[arg-type]


def test_field_accepts_the_exact_boundaries() -> None:
    assert ScentField(GRID, GRID, 0, _grid(Decimal("0"))).at(CENTRE) == Decimal("0")
    assert ScentField(GRID, GRID, 0, _grid(Decimal("0.9"))).at(CENTRE) == Decimal("0.9")


def test_field_accepts_values_inside_the_range() -> None:
    assert ScentField(GRID, GRID, 0, _grid(Decimal("0.4321"))).at(CENTRE) == Decimal("0.4321")


@pytest.mark.parametrize("value", [0.5, "0.5", None, 1])
def test_field_rejects_non_decimal_cells(value: object) -> None:
    with pytest.raises(InvalidScentError):
        ScentField(GRID, GRID, 0, _grid(value))  # type: ignore[arg-type]


@pytest.mark.parametrize("value", ["NaN", "Infinity", "-Infinity"])
def test_field_rejects_non_finite_cells(value: str) -> None:
    with pytest.raises(InvalidScentError):
        ScentField(GRID, GRID, 0, _grid(Decimal(value)))  # type: ignore[arg-type]


def test_re_emission_saturates_at_the_state_bound() -> None:
    # 0.9 decays to 0.81, re-emission adds 0.9 -> raw 1.71 -> saturated 0.9.
    field = ScentField.zero(BOARD).evolve(CENTRE_ONLY, (CENTRE,), PARAMS)
    assert field.at(CENTRE) == Decimal("0.9")
    field = field.evolve(CENTRE_ONLY, (CENTRE,), PARAMS)
    assert field.at(CENTRE) == Decimal("0.9")
    assert field.at(CENTRE) != Decimal("1.71")


def test_a_raw_result_below_the_bound_stays_exactly_additive() -> None:
    # Saturation is a boundary operation, never a replacement of the recurrence.
    field = ScentField.zero(BOARD).evolve(HALF_KERNEL, (CENTRE,), PARAMS)
    neighbour = Position(3, 4)
    assert field.at(neighbour) == Decimal("0.2")
    field = field.evolve(HALF_KERNEL, (CENTRE,), PARAMS)
    # 0.9 * 0.2 + 0.2 = 0.38, comfortably below the bound.
    assert field.at(neighbour) == Decimal("0.38")


def test_the_lower_clamp_still_applies() -> None:
    field = ScentField.zero(BOARD).evolve(CENTRE_ONLY, (CENTRE,), PARAMS)
    for _ in range(60):
        field = field.evolve(CENTRE_ONLY, (), PARAMS)
    assert field.at(CENTRE) >= Decimal("0")
    assert all(value >= 0 for row in field.values for value in row)


def test_every_evolved_cell_stays_inside_the_state_domain() -> None:
    field = ScentField.zero(BOARD)
    sources = (Position(2, 2), Position(3, 3), Position(4, 4))
    for _ in range(6):
        field = field.evolve(HALF_KERNEL, sources, PARAMS)
        for row in field.values:
            for value in row:
                assert Decimal("0") <= value <= MAX_SCENT_STATE


def test_overlapping_sources_saturate_deterministically() -> None:
    # Three overlapping emitters would sum well past 0.9 on the shared cells.
    sources = (Position(3, 3), Position(3, 4), Position(4, 3))
    field = ScentField.zero(BOARD).evolve(HALF_KERNEL, sources, PARAMS)
    assert field.at(Position(3, 3)) == Decimal("0.9")
    assert field.at(Position(3, 4)) == Decimal("0.9")
    assert all(value <= MAX_SCENT_STATE for row in field.values for value in row)


def test_source_order_does_not_change_the_saturated_field() -> None:
    sources = (Position(3, 3), Position(3, 4), Position(4, 3))
    base = ScentField.zero(BOARD)
    results = {
        base.evolve(HALF_KERNEL, order, PARAMS)
        for order in (sources, tuple(reversed(sources)), (sources[1], sources[2], sources[0]))
    }
    assert len(results) == 1


def test_kernel_weights_cannot_exceed_the_centre() -> None:
    # Structural consequence of centre 0.9 plus radial non-increase.
    for kernel in (CENTRE_ONLY, HALF_KERNEL):
        for d_row in (-2, -1, 0, 1, 2):
            for d_col in (-2, -1, 0, 1, 2):
                assert kernel.weight_at(d_row, d_col) <= MAX_SCENT_STATE
