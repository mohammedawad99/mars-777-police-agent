"""Unit tests for the immutable grid configuration value object.

Covers PRD01-FR-001 (square grid, size read from config, size < 7 rejected),
PRD01-FR-002 (axis start index) and PRD01-NFR-001 (pure, immutable domain).
Stage 3A: grid geometry policy only -- not the 39-field config artifact.
"""

import dataclasses

import pytest

from mars777_police.domain.board import Board
from mars777_police.domain.config_model import (
    MIN_GRID_SIZE,
    GridConfig,
    InvalidGridConfigError,
)
from mars777_police.domain.errors import DomainError


def test_minimum_grid_size_is_the_locked_floor() -> None:
    # App F T13 grid_size MINIMUM 7 / C-01. The floor is a validation bound;
    # the actual size still comes from the signed config.
    assert MIN_GRID_SIZE == 7


def test_seven_by_seven_is_accepted() -> None:
    cfg = GridConfig(rows=7, cols=7)
    assert (cfg.rows, cfg.cols, cfg.start_index) == (7, 7, 0)


@pytest.mark.parametrize("size", [8, 9, 12, 40])
def test_larger_grids_are_accepted(size: int) -> None:
    cfg = GridConfig(rows=size, cols=size)
    assert (cfg.rows, cfg.cols) == (size, size)


@pytest.mark.parametrize("rows", [6, 5, 1, 0, -7])
def test_rows_below_minimum_are_rejected(rows: int) -> None:
    with pytest.raises(InvalidGridConfigError):
        GridConfig(rows=rows, cols=7)


@pytest.mark.parametrize("cols", [6, 5, 1, 0, -7])
def test_cols_below_minimum_are_rejected(cols: int) -> None:
    with pytest.raises(InvalidGridConfigError):
        GridConfig(rows=7, cols=cols)


@pytest.mark.parametrize("value", ["7", 7.0, None, True, [7], (7,)])
def test_malformed_dimensions_are_rejected_not_coerced(value: object) -> None:
    with pytest.raises(InvalidGridConfigError):
        GridConfig(rows=value, cols=7)  # type: ignore[arg-type]
    with pytest.raises(InvalidGridConfigError):
        GridConfig(rows=7, cols=value)  # type: ignore[arg-type]


@pytest.mark.parametrize("value", ["0", 0.0, None, True])
def test_malformed_start_index_is_rejected(value: object) -> None:
    with pytest.raises(InvalidGridConfigError):
        GridConfig(rows=7, cols=7, start_index=value)  # type: ignore[arg-type]


def test_negative_start_index_is_rejected() -> None:
    with pytest.raises(InvalidGridConfigError):
        GridConfig(rows=7, cols=7, start_index=-1)


def test_non_square_grid_is_rejected() -> None:
    # PRD01-FR-001: the board is a SQUARE grid sized by config grid_size.
    with pytest.raises(InvalidGridConfigError):
        GridConfig(rows=7, cols=8)
    with pytest.raises(InvalidGridConfigError):
        GridConfig(rows=9, cols=7)


def test_from_grid_size_matches_the_locked_config_shape() -> None:
    assert GridConfig.from_grid_size(9) == GridConfig(rows=9, cols=9)
    assert GridConfig.from_grid_size(9, start_index=1).start_index == 1


def test_from_grid_size_enforces_the_same_floor() -> None:
    with pytest.raises(InvalidGridConfigError):
        GridConfig.from_grid_size(6)


def test_config_is_immutable_with_no_hidden_members() -> None:
    cfg = GridConfig(rows=7, cols=7)
    with pytest.raises(dataclasses.FrozenInstanceError):
        cfg.rows = 9  # type: ignore[misc]
    # Slots: no instance __dict__, so no hidden mutable member can be attached.
    assert not hasattr(cfg, "__dict__")
    assert GridConfig.__slots__ == ("rows", "cols", "start_index")


def test_config_equality_and_hashing() -> None:
    assert GridConfig(7, 7) == GridConfig(7, 7)
    assert GridConfig(7, 7) != GridConfig(8, 8)
    assert len({GridConfig(7, 7), GridConfig(7, 7), GridConfig(8, 8)}) == 2


def test_invalid_config_error_is_a_domain_error() -> None:
    assert issubclass(InvalidGridConfigError, DomainError)


def test_to_board_uses_the_configured_geometry() -> None:
    board = GridConfig(rows=7, cols=7, start_index=1).to_board()
    assert isinstance(board, Board)
    assert (board.rows, board.cols, board.start_index) == (7, 7, 1)
    assert board.blocked == frozenset()


def test_the_minimum_floor_is_a_config_policy_not_a_geometry_rule() -> None:
    # Documented seam: domain.board is policy-free geometry (stdlib only, per
    # MODULE_BOUNDARIES), and GridConfig is the only gate a signed config
    # passes through. A sub-minimum board is therefore reachable in geometry
    # but never via the configuration path.
    assert Board(rows=3, cols=3).rows == 3
    with pytest.raises(InvalidGridConfigError):
        GridConfig(rows=3, cols=3)
    with pytest.raises(InvalidGridConfigError):
        GridConfig.from_grid_size(3).to_board()
