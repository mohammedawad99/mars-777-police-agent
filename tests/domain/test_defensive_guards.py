"""Defensive-input guards across the Stage-3B domain modules.

The domain is fed by protocol and orchestration layers that do not exist yet,
so every public entry point rejects a wrong-typed argument deterministically
instead of raising an incidental AttributeError or TypeError. These are the
negative paths that ordinary rule tests never reach.
"""

from decimal import Decimal

import pytest

from mars777_police.domain.barriers import (
    BarrierQuota,
    InvalidBarrierError,
    _cell,
    is_adjacent_or_same,
    is_placeable,
)
from mars777_police.domain.board import Board, InvalidBoardError, Position
from mars777_police.domain.config_model import InvalidScentError, require_decimal
from mars777_police.domain.scent import ScentField, ScentKernel, ScentParams
from mars777_police.domain.terminal import (
    InvalidTurnLimitsError,
    TurnLimits,
    evaluate_terminal,
    is_same_cell,
    is_trapped,
)

GRID = 7
CENTRE = Position(3, 3)
BOARD = Board(rows=GRID, cols=GRID)
QUOTA = BarrierQuota(max_barriers=14)
KERNEL = ScentKernel.from_rows(
    tuple(tuple("0.9" if (r, c) == (2, 2) else "0" for c in range(5)) for r in range(5)),
)


@pytest.mark.parametrize("value", [(3, 3), None, "3,3", 3])
def test_adjacency_rejects_non_positions(value: object) -> None:
    assert not is_adjacent_or_same(value, CENTRE)  # type: ignore[arg-type]
    assert not is_adjacent_or_same(CENTRE, value)  # type: ignore[arg-type]


def test_placement_rejects_a_non_board_and_a_non_quota() -> None:
    assert not is_placeable("board", CENTRE, CENTRE, QUOTA)  # type: ignore[arg-type]
    assert not is_placeable(BOARD, CENTRE, CENTRE, 14)  # type: ignore[arg-type]


def test_barrier_error_message_renders_a_non_position_safely() -> None:
    assert _cell((3, 3)) == "<tuple>"
    assert _cell(CENTRE) == "[3,3]"


def test_orthogonal_neighbours_rejects_a_non_position() -> None:
    with pytest.raises(InvalidBoardError):
        BOARD.orthogonal_neighbours((3, 3))  # type: ignore[arg-type]


def test_orthogonal_neighbours_returns_four_cells_in_fixed_order() -> None:
    assert BOARD.orthogonal_neighbours(CENTRE) == (
        Position(2, 3),
        Position(4, 3),
        Position(3, 4),
        Position(3, 2),
    )


def test_require_decimal_rejects_a_non_finite_value() -> None:
    with pytest.raises(InvalidScentError):
        require_decimal(Decimal("NaN"), "probe")
    with pytest.raises(InvalidScentError):
        require_decimal("Infinity", "probe", allow_str=True)


def test_require_decimal_rejects_an_unparsable_string() -> None:
    with pytest.raises(InvalidScentError):
        require_decimal("not-a-number", "probe", allow_str=True)


@pytest.mark.parametrize("rows", ["12345", 5, None])
def test_kernel_rejects_a_non_sequence_of_rows(rows: object) -> None:
    with pytest.raises(InvalidScentError):
        ScentKernel.from_rows(rows)  # type: ignore[arg-type]


def test_kernel_rejects_a_string_row() -> None:
    with pytest.raises(InvalidScentError):
        ScentKernel.from_rows(("00000", "00000", "00000", "00000", "00000"))


def test_kernel_offset_outside_the_window_is_rejected() -> None:
    with pytest.raises(InvalidScentError):
        KERNEL.weight_at(3, 0)
    with pytest.raises(InvalidScentError):
        KERNEL.weight_at(0, -3)


def test_zero_field_requires_a_board() -> None:
    with pytest.raises(InvalidScentError):
        ScentField.zero("board")  # type: ignore[arg-type]


def test_evolve_requires_a_kernel_and_params() -> None:
    field = ScentField.zero(BOARD)
    with pytest.raises(InvalidScentError):
        field.evolve("kernel", (CENTRE,), ScentParams())  # type: ignore[arg-type]
    with pytest.raises(InvalidScentError):
        field.evolve(KERNEL, (CENTRE,), "params")  # type: ignore[arg-type]
    with pytest.raises(InvalidScentError, match="absorbing an emission needs ScentParams"):
        field.absorb({}, "params")  # type: ignore[arg-type]


def test_field_index_rejects_a_non_position() -> None:
    with pytest.raises(InvalidScentError):
        ScentField.zero(BOARD).at((3, 3))  # type: ignore[arg-type]


@pytest.mark.parametrize("value", [(3, 3), None, "cell"])
def test_same_cell_rejects_non_positions(value: object) -> None:
    assert not is_same_cell(value, CENTRE)  # type: ignore[arg-type]
    assert not is_same_cell(CENTRE, value)  # type: ignore[arg-type]


def test_trapped_rejects_a_non_board_or_non_position() -> None:
    assert not is_trapped("board", CENTRE)  # type: ignore[arg-type]
    assert not is_trapped(BOARD, (3, 3))  # type: ignore[arg-type]


def test_evaluate_terminal_requires_real_turn_limits() -> None:
    with pytest.raises(InvalidTurnLimitsError):
        evaluate_terminal(captured=False, step=1, limits=(35, 35))  # type: ignore[arg-type]
    assert evaluate_terminal(captured=False, step=1, limits=TurnLimits(35, 35)) is None


def test_barrier_quota_guard_is_a_domain_error() -> None:
    with pytest.raises(InvalidBarrierError):
        BarrierQuota(max_barriers=1)
