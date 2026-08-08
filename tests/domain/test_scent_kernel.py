"""Unit tests for the agreed 5x5 emission kernel and its radial contract.

Ch 4 p.43 / Figure 4 give only a radial fall-off and App F T16 locks just the
centre 0.9 and the 5x5 window, so an agreed kernel is validated against that
description. The illustrative Figure-4 matrix is a test fixture only.
"""

import inspect
from decimal import Decimal

import pytest

from mars777_police.domain import scent, scent_kernel
from mars777_police.domain.config_model import InvalidScentError
from mars777_police.domain.errors import DomainError
from mars777_police.domain.scent_kernel import ScentKernel

CENTRE_ONLY = (
    ("0", "0", "0", "0", "0"),
    ("0", "0", "0", "0", "0"),
    ("0", "0", "0.9", "0", "0"),
    ("0", "0", "0", "0", "0"),
    ("0", "0", "0", "0", "0"),
)


def test_kernel_from_the_locked_constraints_is_accepted() -> None:
    kernel = ScentKernel.from_rows(CENTRE_ONLY)
    assert len(kernel.weights) == 5
    assert kernel.center == Decimal("0.9")
    assert kernel.weight_at(0, 0) == Decimal("0.9")
    assert kernel.weight_at(-2, -2) == Decimal("0")


def test_kernel_accepts_a_radial_fall_off_shape() -> None:
    rows = (
        ("0.04", "0.14", "0.20", "0.14", "0.04"),
        ("0.14", "0.42", "0.62", "0.42", "0.14"),
        ("0.20", "0.62", "0.9", "0.62", "0.20"),
        ("0.14", "0.42", "0.62", "0.42", "0.14"),
        ("0.04", "0.14", "0.20", "0.14", "0.04"),
    )
    kernel = ScentKernel.from_rows(rows)
    assert kernel.center == Decimal("0.9")
    assert kernel.weight_at(0, 1) == Decimal("0.62")


def test_kernel_wrong_dimensions_are_rejected() -> None:
    with pytest.raises(InvalidScentError):
        ScentKernel.from_rows(tuple(CENTRE_ONLY[:4]))
    with pytest.raises(InvalidScentError):
        ScentKernel.from_rows(tuple(row[:4] for row in CENTRE_ONLY))


def test_kernel_wrong_centre_is_rejected() -> None:
    bad = tuple(
        tuple("0.5" if (r, c) == (2, 2) else v for c, v in enumerate(row))
        for r, row in enumerate(CENTRE_ONLY)
    )
    with pytest.raises(InvalidScentError):
        ScentKernel.from_rows(bad)


def test_kernel_negative_and_malformed_weights_are_rejected() -> None:
    for bad_value in ("-0.1", "abc", None, 0.5):
        bad = tuple(
            tuple(bad_value if (r, c) == (0, 0) else v for c, v in enumerate(row))
            for r, row in enumerate(CENTRE_ONLY)
        )
        with pytest.raises(InvalidScentError):
            ScentKernel.from_rows(bad)  # type: ignore[arg-type]


def test_reference_only_key_is_absent() -> None:
    for module in (scent, scent_kernel):
        assert not any("min_center" in name for name in dir(module))


def test_scent_errors_are_domain_errors() -> None:
    assert issubclass(InvalidScentError, DomainError)


FIGURE_4 = (
    ("0.04", "0.14", "0.20", "0.14", "0.04"),
    ("0.14", "0.42", "0.62", "0.42", "0.14"),
    ("0.20", "0.62", "0.90", "0.62", "0.20"),
    ("0.14", "0.42", "0.62", "0.42", "0.14"),
    ("0.04", "0.14", "0.20", "0.14", "0.04"),
)
FLAT_RADIAL = (
    ("0.1", "0.1", "0.1", "0.1", "0.1"),
    ("0.1", "0.5", "0.5", "0.5", "0.1"),
    ("0.1", "0.5", "0.9", "0.5", "0.1"),
    ("0.1", "0.5", "0.5", "0.5", "0.1"),
    ("0.1", "0.1", "0.1", "0.1", "0.1"),
)


def test_figure_4_is_one_valid_radial_kernel_among_others() -> None:
    # Figure 4 validates, and so does a different radial shape: the illustrative
    # numbers are one accepted example, never a hard-coded requirement.
    assert ScentKernel.from_rows(FIGURE_4).center == Decimal("0.9")
    assert ScentKernel.from_rows(FIGURE_4).weight_at(0, 1) == Decimal("0.62")
    assert ScentKernel.from_rows(FLAT_RADIAL).weight_at(0, 1) == Decimal("0.5")


def test_production_does_not_embed_the_illustrative_matrix() -> None:
    source = inspect.getsource(scent)
    for value in ("0.04", "0.14", "0.20", "0.42", "0.62"):
        assert value not in source


def test_equal_radius_cells_must_be_equal() -> None:
    rows = [list(r) for r in FIGURE_4]
    rows[1][2] = "0.61"  # squared radius 1, no longer equal to its ring
    with pytest.raises(InvalidScentError):
        ScentKernel.from_rows(tuple(tuple(r) for r in rows))


def test_a_farther_ring_may_not_be_stronger_than_a_nearer_ring() -> None:
    rows = [list(r) for r in FIGURE_4]
    for r, c in ((0, 0), (0, 4), (4, 0), (4, 4)):  # squared radius 8
        rows[r][c] = "0.70"
    with pytest.raises(InvalidScentError):
        ScentKernel.from_rows(tuple(tuple(r) for r in rows))


def test_equal_intensity_on_adjacent_rings_is_allowed() -> None:
    # Non-increasing, not strictly decreasing: the source fixes no curve.
    rows = [list(r) for r in FIGURE_4]
    rows[0][1] = rows[0][3] = rows[1][0] = rows[1][4] = "0.20"
    rows[3][0] = rows[3][4] = rows[4][1] = rows[4][3] = "0.20"
    assert ScentKernel.from_rows(tuple(tuple(r) for r in rows)).weight_at(-2, -1) == Decimal("0.20")


def test_an_arbitrary_non_negative_matrix_is_rejected() -> None:
    arbitrary = tuple(
        tuple("0.9" if (r, c) == (2, 2) else str((r * 5 + c) / 100) for c in range(5))
        for r in range(5)
    )
    with pytest.raises(InvalidScentError):
        ScentKernel.from_rows(arbitrary)


def test_kernel_from_different_containers_is_canonically_equal() -> None:
    assert ScentKernel.from_rows(FIGURE_4) == ScentKernel.from_rows([list(row) for row in FIGURE_4])
    assert ScentKernel.from_rows(CENTRE_ONLY) == ScentKernel.from_rows(list(CENTRE_ONLY))
    assert isinstance(ScentKernel.from_rows(CENTRE_ONLY).weights, tuple)
