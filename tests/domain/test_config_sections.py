"""Board, world, movement and scoring config sections."""

import pytest
from config_builders import board, movement, scoring, world

from mars777_police.domain.board import Position
from mars777_police.domain.config_sections import (
    BoardAndAgentsTerms,
    InvalidConfigSectionError,
    MovementAndBarrierTerms,
    ScoringTerms,
    WorldTerms,
)


def test_valid_sections() -> None:
    assert board().grid_size == 7
    assert world().hint_max_words == 15
    assert movement().max_moves == 35
    assert scoring().capture_cop == 20


def test_grid_size_minimum_boundary() -> None:
    assert board(grid_size=7).grid_size == 7
    with pytest.raises(InvalidConfigSectionError, match="grid_size must be >= 7"):
        board(grid_size=6)


@pytest.mark.parametrize("bad", [True, "7", 7.0])
def test_grid_size_is_strict_int(bad: object) -> None:
    with pytest.raises(InvalidConfigSectionError, match="grid_size must be an int"):
        board(grid_size=bad)


def test_num_agents_is_fixed_at_two() -> None:
    with pytest.raises(InvalidConfigSectionError, match="num_agents is FIXED at 2"):
        board(num_agents=3)


@pytest.mark.parametrize("bad", ["", None, 1])
def test_axis_origin_corner_must_be_non_empty_str(bad: object) -> None:
    with pytest.raises(InvalidConfigSectionError, match="axis_origin_corner"):
        board(axis_origin_corner=bad)


def test_axis_start_index_floor() -> None:
    with pytest.raises(InvalidConfigSectionError, match="axis_start_index must be >= 0"):
        board(axis_start_index=-1)


@pytest.mark.parametrize("field", ["thief_start", "cop_start"])
def test_start_cells_must_be_positions(field: str) -> None:
    with pytest.raises(InvalidConfigSectionError, match=f"{field} must be a Position"):
        board(**{field: (0, 0)})


@pytest.mark.parametrize("field", ["thief_start", "cop_start"])
def test_start_cells_must_be_inside_the_board(field: str) -> None:
    with pytest.raises(InvalidConfigSectionError, match="outside the declared board"):
        board(**{field: Position(7, 0)})


def test_start_cells_must_differ() -> None:
    with pytest.raises(InvalidConfigSectionError, match="must differ"):
        board(thief_start=Position(0, 0), cop_start=Position(0, 0))


@pytest.mark.parametrize("bad", [None, 1])
def test_map_area_must_be_str(bad: object) -> None:
    with pytest.raises(InvalidConfigSectionError, match="map_area must be a str"):
        world(map_area=bad)


def test_empty_map_area_is_the_generic_map() -> None:
    assert world(map_area="").map_area == ""


def test_hint_max_words_floor() -> None:
    with pytest.raises(InvalidConfigSectionError, match="hint_max_words must be >= 1"):
        world(hint_max_words=0)


@pytest.mark.parametrize("bad", [["N"], None, "NSEW"])
def test_move_set_must_be_a_tuple(bad: object) -> None:
    with pytest.raises(InvalidConfigSectionError, match="move_set must be a tuple"):
        movement(move_set=bad)


def test_move_set_is_fixed_including_order() -> None:
    with pytest.raises(InvalidConfigSectionError, match="move_set is FIXED"):
        movement(move_set=("N", "S", "E", "STAY", "W"))


@pytest.mark.parametrize(
    ("field", "floor"),
    [("max_barriers", 14), ("max_moves", 35), ("survival_threshold", 35)],
)
def test_movement_minimum_boundaries(field: str, floor: int) -> None:
    assert getattr(movement(**{field: floor}), field) == floor
    with pytest.raises(InvalidConfigSectionError, match=f"{field} must be >= {floor}"):
        movement(**{field: floor - 1})


def test_survival_threshold_may_not_exceed_max_moves() -> None:
    assert movement(max_moves=40, survival_threshold=40).survival_threshold == 40
    with pytest.raises(InvalidConfigSectionError, match="JDEC-015"):
        movement(max_moves=35, survival_threshold=36)


@pytest.mark.parametrize(
    ("field", "locked"),
    [
        ("capture_cop", 20),
        ("capture_thief", 5),
        ("survival_cop", 5),
        ("survival_thief", 10),
        ("tie_score", 2),
        ("technical_loss", 0),
    ],
)
def test_every_scoring_value_is_fixed(field: str, locked: int) -> None:
    with pytest.raises(InvalidConfigSectionError, match=f"{field} is FIXED at {locked}"):
        scoring(**{field: locked + 1})


def test_scoring_rejects_bool() -> None:
    with pytest.raises(InvalidConfigSectionError, match="must be an int"):
        scoring(tie_score=True)


def test_sections_are_immutable() -> None:
    for value in (board(), world(), movement(), scoring()):
        assert type(value) in (
            BoardAndAgentsTerms,
            WorldTerms,
            MovementAndBarrierTerms,
            ScoringTerms,
        )
