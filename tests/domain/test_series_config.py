"""The counted-series length is **FIXED at 6**, not a floor.

App F Table 18 #1 gives `num_games` the value **6** with status **FIXED**, and
Appendix F defines FIXED (קבוע) as "binding, unchangeable; **deviation
disqualifies**" - so 7 is as illegal as 5. That is the whole difference from a
MINIMUM row such as `grid_size` (7), which this module deliberately still
accepts above its floor. C-05 closes the App B `num_games: 1` demo default as
illustrative; INV-09 restates 6 FIXED.

Sub-games are numbered from 1 (`FIRST_SUB_GAME`): JDEC-004 writes `g01`...`g06`
and both the log and result contracts carry `"sub_game": 1`.
"""

import dataclasses

import pytest

from mars777_police.domain.config_model import (
    FIRST_SUB_GAME,
    FIXED_NUM_GAMES,
    InvalidSeriesError,
    SeriesConfig,
)


def test_the_counted_series_length_is_the_fixed_appendix_f_value() -> None:
    assert FIXED_NUM_GAMES == 6


def test_sub_games_are_numbered_from_one() -> None:
    assert FIRST_SUB_GAME == 1


def test_the_default_series_is_the_counted_six() -> None:
    assert SeriesConfig().num_games == 6


def test_the_exact_fixed_value_is_accepted() -> None:
    assert SeriesConfig(num_games=6).num_games == 6


@pytest.mark.parametrize("value", [7, 10, 12, 100])
def test_a_longer_series_is_refused_because_the_row_is_fixed(value: int) -> None:
    """Deviation upward disqualifies too - this is not a MINIMUM row."""
    with pytest.raises(InvalidSeriesError, match="FIXED"):
        SeriesConfig(num_games=value)


@pytest.mark.parametrize("value", [5, 1, 0, -1])
def test_a_shorter_series_is_refused(value: int) -> None:
    with pytest.raises(InvalidSeriesError, match="FIXED"):
        SeriesConfig(num_games=value)


@pytest.mark.parametrize("value", [True, False, 6.0, "6", None, Ellipsis])
def test_a_non_integer_count_is_refused(value: object) -> None:
    with pytest.raises(InvalidSeriesError):
        SeriesConfig(num_games=value)  # type: ignore[arg-type]


def test_the_series_config_is_frozen_slotted_and_value_equal() -> None:
    series = SeriesConfig()
    with pytest.raises(dataclasses.FrozenInstanceError):
        series.num_games = 7  # type: ignore[misc]
    assert not hasattr(series, "__dict__")
    assert SeriesConfig.__slots__ == ("num_games",)
    assert series == SeriesConfig(num_games=6)


def test_the_series_config_carries_exactly_one_field() -> None:
    """One fact, one representation - no total_games/series_length/max_subgames."""
    assert tuple(f.name for f in dataclasses.fields(SeriesConfig)) == ("num_games",)


def test_no_alias_and_no_minimum_name_survive() -> None:
    from mars777_police.domain import config_model

    for alias in ("MIN_NUM_GAMES", "MAX_NUM_GAMES", "MIN_SERIES_LENGTH", "NUM_GAMES"):
        assert not hasattr(config_model, alias)
    for alias in ("total_games", "num_subgames", "series_length", "max_subgames"):
        assert not hasattr(config_model, alias)
        assert not hasattr(SeriesConfig, alias)


def test_the_fixed_six_has_exactly_one_production_definition() -> None:
    """The literal 6 lives in one constant; nothing re-states it."""
    import ast
    import pathlib

    from mars777_police.app import orchestrator

    for module in (config_source(), pathlib.Path(orchestrator.__file__).read_text()):
        sixes = [
            n
            for n in ast.walk(ast.parse(module))
            if isinstance(n, ast.Constant) and n.value == 6 and not isinstance(n.value, bool)
        ]
        assert len(sixes) <= 1


def config_source() -> str:
    import pathlib

    from mars777_police.domain import config_model

    return pathlib.Path(config_model.__file__).read_text()
