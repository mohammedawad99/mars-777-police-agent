"""Unit tests for the deterministic scent field physics.

SCENT-002 / PRD01-FR-040…043: tau(t+1) = max(0, (1-rho)*tau(t) + delta_tau),
rho = 0.10 FIXED, emission window 5x5 FIXED, clamped at zero and never
negative. Decimal arithmetic makes 0.9 -> 0.81 exact, so cross-platform
equality is a contract rather than an approximation.
"""

from decimal import Decimal

import pytest

from mars777_police.domain.board import Board, Position
from mars777_police.domain.scent import (
    InvalidScentError,
    ScentField,
    ScentKernel,
    ScentParams,
)

GRID = 7
LAST = GRID - 1
CENTRE = Position(3, 3)
PARAMS = ScentParams()
BOARD = Board(rows=GRID, cols=GRID)

CENTRE_ONLY = ScentKernel.from_rows(
    (
        ("0", "0", "0", "0", "0"),
        ("0", "0", "0", "0", "0"),
        ("0", "0", "0.9", "0", "0"),
        ("0", "0", "0", "0", "0"),
        ("0", "0", "0", "0", "0"),
    ),
)
RADIAL = ScentKernel.from_rows(
    (
        ("0.0", "0.1", "0.2", "0.1", "0.0"),
        ("0.1", "0.3", "0.5", "0.3", "0.1"),
        ("0.2", "0.5", "0.9", "0.5", "0.2"),
        ("0.1", "0.3", "0.5", "0.3", "0.1"),
        ("0.0", "0.1", "0.2", "0.1", "0.0"),
    ),
)


def test_zero_field_is_all_zero() -> None:
    field = ScentField.zero(BOARD)
    assert field.at(CENTRE) == Decimal("0")
    assert all(value == 0 for row in field.values for value in row)


def test_emission_writes_the_centre_intensity() -> None:
    field = ScentField.zero(BOARD).evolve(CENTRE_ONLY, (CENTRE,), PARAMS)
    assert field.at(CENTRE) == Decimal("0.9")
    assert field.at(Position(3, 4)) == Decimal("0")


def test_one_decay_step_is_exactly_zero_point_eight_one() -> None:
    emitted = ScentField.zero(BOARD).evolve(CENTRE_ONLY, (CENTRE,), PARAMS)
    decayed = emitted.evolve(CENTRE_ONLY, (), PARAMS)
    assert decayed.at(CENTRE) == Decimal("0.81")


def test_repeated_decay_is_exact() -> None:
    field = ScentField.zero(BOARD).evolve(CENTRE_ONLY, (CENTRE,), PARAMS)
    expected = ("0.81", "0.729", "0.6561", "0.59049")
    for want in expected:
        field = field.evolve(CENTRE_ONLY, (), PARAMS)
        assert field.at(CENTRE) == Decimal(want)


def test_repeated_re_emission_stays_inside_the_state_domain() -> None:
    # C-10: raw 0.81 + 0.9 = 1.71 leaves the [0, 0.9] state domain, so it saturates.
    field = ScentField.zero(BOARD).evolve(CENTRE_ONLY, (CENTRE,), PARAMS)
    field = field.evolve(CENTRE_ONLY, (CENTRE,), PARAMS)
    assert field.at(CENTRE) == Decimal("0.9")


def test_values_are_clamped_at_zero_and_never_negative() -> None:
    field = ScentField.zero(BOARD).evolve(CENTRE_ONLY, (CENTRE,), PARAMS)
    for _ in range(40):
        field = field.evolve(CENTRE_ONLY, (), PARAMS)
    assert field.at(CENTRE) >= 0
    assert all(value >= 0 for row in field.values for value in row)


def test_emission_is_clipped_at_a_corner_without_wrapping() -> None:
    corner = Position(0, 0)
    field = ScentField.zero(BOARD).evolve(RADIAL, (corner,), PARAMS)
    assert field.at(corner) == Decimal("0.9")
    assert field.at(Position(0, 1)) == Decimal("0.5")
    assert field.at(Position(1, 0)) == Decimal("0.5")
    # No wrap-around onto the opposite edges.
    assert field.at(Position(LAST, LAST)) == Decimal("0")
    assert field.at(Position(0, LAST)) == Decimal("0")
    assert field.at(Position(LAST, 0)) == Decimal("0")


def test_emission_near_an_edge_only_touches_in_board_cells() -> None:
    f = ScentField.zero(BOARD).evolve(RADIAL, (Position(0, 3),), PARAMS)
    assert (f.at(Position(0, 3)), f.at(Position(1, 3))) == (Decimal("0.9"), Decimal("0.5"))
    assert f.at(Position(LAST, 3)) == Decimal("0")


def test_source_ordering_does_not_change_the_result() -> None:
    sources = (Position(2, 2), Position(4, 4), Position(3, 5))
    base = ScentField.zero(BOARD)
    results = {
        base.evolve(RADIAL, order, PARAMS)
        for order in (sources, tuple(reversed(sources)), (sources[1], sources[2], sources[0]))
    }
    assert len(results) == 1


def test_evolution_does_not_mutate_the_input_field() -> None:
    field = ScentField.zero(BOARD)
    field.evolve(RADIAL, (CENTRE,), PARAMS)
    assert field.at(CENTRE) == Decimal("0")
    assert field == ScentField.zero(BOARD)


def test_field_is_deterministically_iterable_and_stable() -> None:
    field = ScentField.zero(BOARD).evolve(RADIAL, (CENTRE,), PARAMS)
    assert isinstance(field.values, tuple)
    assert all(isinstance(row, tuple) for row in field.values)
    assert [field.at(p) for p in (CENTRE, Position(3, 4))] == [Decimal("0.9"), Decimal("0.5")]


def test_off_board_source_is_rejected() -> None:
    with pytest.raises(InvalidScentError):
        ScentField.zero(BOARD).evolve(RADIAL, (Position(-1, 0),), PARAMS)


def test_off_board_query_is_rejected() -> None:
    with pytest.raises(InvalidScentError):
        ScentField.zero(BOARD).at(Position(GRID, 0))


def test_both_roles_share_one_physical_model() -> None:
    # There is exactly one evolve implementation; no role parameter exists.
    assert "role" not in ScentField.evolve.__code__.co_varnames


def test_values_use_one_canonical_representation() -> None:
    field = ScentField.zero(BOARD).evolve(CENTRE_ONLY, (CENTRE,), PARAMS)
    assert str(field.at(CENTRE)) == "0.9"
    assert str(field.at(Position(0, 0))) == "0"
    decayed = field.evolve(CENTRE_ONLY, (), PARAMS)
    assert str(decayed.at(CENTRE)) == "0.81"
