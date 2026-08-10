"""Pheromone, league and rate-limiter config sections."""

from decimal import Decimal

import pytest
from config_builders import league, pheromones, rate_limiter

from mars777_police.domain.config_league_sections import NetworkAndLeagueTerms
from mars777_police.domain.config_model import InvalidScentError, InvalidSeriesError
from mars777_police.domain.config_sections import InvalidConfigSectionError


def test_valid_sections() -> None:
    assert pheromones().pheromone_grid_size == 5
    assert league().num_games == 6
    assert rate_limiter().queue_depth == 100


@pytest.mark.parametrize(
    ("field", "bad"),
    [
        ("pheromone_center_intensity", Decimal("0.8")),
        ("pheromone_decay", Decimal("0.11")),
        ("pheromone_grid_size", 4),
    ],
)
def test_pheromone_values_are_fixed(field: str, bad: object) -> None:
    with pytest.raises(InvalidScentError):
        pheromones(**{field: bad})


def test_pheromone_rejects_float() -> None:
    with pytest.raises(InvalidScentError, match="must be a Decimal"):
        pheromones(pheromone_center_intensity=0.9)


def test_num_games_is_fixed_at_six() -> None:
    with pytest.raises(InvalidSeriesError, match="num_games is FIXED at 6"):
        league(num_games=7)


@pytest.mark.parametrize(
    ("field", "locked"),
    [("diversity_reward", 10), ("min_games_to_pass", 2), ("max_games_per_team", 10)],
)
def test_league_fixed_values(field: str, locked: int) -> None:
    with pytest.raises(InvalidConfigSectionError, match=f"{field} is FIXED at {locked}"):
        league(**{field: locked + 1})


@pytest.mark.parametrize("field", ["response_timeout_sec", "watchdog_timeout_sec"])
def test_league_timeouts_must_be_positive(field: str) -> None:
    with pytest.raises(InvalidConfigSectionError, match=f"{field} must be >= 1"):
        league(**{field: 0})


def test_token_budget_must_be_positive() -> None:
    with pytest.raises(InvalidConfigSectionError, match="token_budget_per_series must be >= 1"):
        league(token_budget_per_series=0)


def test_token_budget_stores_any_agreed_positive_value() -> None:
    assert league(token_budget_per_series=1).token_budget_per_series == 1
    assert isinstance(league(), NetworkAndLeagueTerms)


@pytest.mark.parametrize(
    ("field", "floor"),
    [
        ("requests_per_minute", 30),
        ("concurrent_requests", 2),
        ("retry_backoff_sec", 5),
        ("max_retries", 3),
        ("queue_depth", 100),
    ],
)
def test_rate_limiter_minimum_boundaries(field: str, floor: int) -> None:
    assert getattr(rate_limiter(**{field: floor}), field) == floor
    with pytest.raises(InvalidConfigSectionError, match=f"{field} must be >= {floor}"):
        rate_limiter(**{field: floor - 1})


@pytest.mark.parametrize("field", ["requests_per_minute", "queue_depth"])
def test_rate_limiter_rejects_bool(field: str) -> None:
    with pytest.raises(InvalidConfigSectionError, match="must be an int"):
        rate_limiter(**{field: True})
