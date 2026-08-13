"""The value that carries one turn's scent contribution across the wire.

Canonical or refused: the final audit re-renders an emission from the disclosed
trajectory and compares it exactly, so a second spelling of the same physics
would be a second answer to one question.
"""

from decimal import Decimal

import pytest

from mars777_police.domain.board import Position
from mars777_police.domain.config_model import InvalidScentError
from mars777_police.domain.scent_emission import ScentDeposit, ScentEmission

HERE = Position(2, 3)
THERE = Position(2, 4)


def deposit(row: int, col: int, value: str = "0.9") -> ScentDeposit:
    return ScentDeposit(Position(row, col), Decimal(value))


def test_an_emission_keeps_its_deposits_in_the_order_it_was_given() -> None:
    emission = ScentEmission((deposit(2, 3), deposit(2, 4, "0.6")))
    assert emission.cells == (HERE, THERE)
    assert emission.at(THERE) == Decimal("0.6")


def test_a_cell_the_emission_never_touched_reads_zero() -> None:
    assert ScentEmission((deposit(2, 3),)).at(Position(6, 6)) == Decimal(0)


def test_an_empty_emission_is_representable_and_touches_nothing() -> None:
    empty = ScentEmission()
    assert empty.deposits == () and empty.cells == ()
    assert empty.at(HERE) == Decimal(0)


@pytest.mark.parametrize(
    ("cell", "intensity", "expected"),
    [
        ("2,3", Decimal("0.9"), "needs a Position"),
        (Position(2, 3), 0.9, "finite Decimal"),
        (Position(2, 3), Decimal("NaN"), "finite Decimal"),
        (Position(2, 3), Decimal(0), "positive intensity"),
        (Position(2, 3), Decimal("-0.1"), "positive intensity"),
    ],
)
def test_a_deposit_is_a_real_cell_with_a_real_positive_intensity(
    cell: object, intensity: object, expected: str
) -> None:
    with pytest.raises(InvalidScentError, match=expected):
        ScentDeposit(cell, intensity)  # type: ignore[arg-type]


def test_the_deposits_must_be_a_tuple() -> None:
    with pytest.raises(InvalidScentError, match="must be a tuple"):
        ScentEmission([deposit(2, 3)])  # type: ignore[arg-type]


def test_every_member_must_be_a_deposit() -> None:
    with pytest.raises(InvalidScentError, match="must be a ScentDeposit"):
        ScentEmission((deposit(2, 3), "0.9"))  # type: ignore[arg-type]


def test_an_out_of_order_emission_is_refused() -> None:
    with pytest.raises(InvalidScentError, match="ordered by"):
        ScentEmission((deposit(2, 4), deposit(2, 3)))


def test_a_repeated_cell_is_refused() -> None:
    with pytest.raises(InvalidScentError, match="unique"):
        ScentEmission((deposit(2, 3), deposit(2, 3, "0.1")))


def test_the_canonical_order_is_row_then_column() -> None:
    assert deposit(2, 3).order == (2, 3)
    assert ScentEmission((deposit(1, 9), deposit(2, 0))).cells == (Position(1, 9), Position(2, 0))
