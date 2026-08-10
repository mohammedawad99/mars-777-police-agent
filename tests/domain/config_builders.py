"""Shared builders for the negotiated-config value tests."""

from decimal import Decimal

from mars777_police.domain.board import Position
from mars777_police.domain.config_league_sections import (
    NetworkAndLeagueTerms,
    PheromoneTerms,
    RateLimiterTerms,
)
from mars777_police.domain.config_sections import (
    BoardAndAgentsTerms,
    MovementAndBarrierTerms,
    ScoringTerms,
    WorldTerms,
)
from mars777_police.domain.negotiated_config import NegotiatedConfig


def board(**over: object) -> BoardAndAgentsTerms:
    fields: dict[str, object] = {
        "grid_size": 7,
        "num_agents": 2,
        "thief_start": Position(3, 3),
        "cop_start": Position(0, 0),
        "axis_origin_corner": "top-left",
        "axis_start_index": 0,
    }
    fields.update(over)
    return BoardAndAgentsTerms(**fields)  # type: ignore[arg-type]


def world(**over: object) -> WorldTerms:
    fields: dict[str, object] = {"map_area": "New York", "hint_max_words": 15}
    fields.update(over)
    return WorldTerms(**fields)  # type: ignore[arg-type]


def movement(**over: object) -> MovementAndBarrierTerms:
    fields: dict[str, object] = {
        "move_set": ("N", "S", "E", "W", "STAY"),
        "max_barriers": 14,
        "max_moves": 35,
        "survival_threshold": 35,
    }
    fields.update(over)
    return MovementAndBarrierTerms(**fields)  # type: ignore[arg-type]


def scoring(**over: object) -> ScoringTerms:
    fields: dict[str, object] = {
        "capture_cop": 20,
        "capture_thief": 5,
        "survival_cop": 5,
        "survival_thief": 10,
        "tie_score": 2,
        "technical_loss": 0,
    }
    fields.update(over)
    return ScoringTerms(**fields)  # type: ignore[arg-type]


def pheromones(**over: object) -> PheromoneTerms:
    fields: dict[str, object] = {
        "pheromone_center_intensity": Decimal("0.9"),
        "pheromone_decay": Decimal("0.10"),
        "pheromone_grid_size": 5,
    }
    fields.update(over)
    return PheromoneTerms(**fields)  # type: ignore[arg-type]


def league(**over: object) -> NetworkAndLeagueTerms:
    fields: dict[str, object] = {
        "response_timeout_sec": 30,
        "watchdog_timeout_sec": 60,
        "num_games": 6,
        "diversity_reward": 10,
        "min_games_to_pass": 2,
        "max_games_per_team": 10,
        "token_budget_per_series": 200000,
    }
    fields.update(over)
    return NetworkAndLeagueTerms(**fields)  # type: ignore[arg-type]


def rate_limiter(**over: object) -> RateLimiterTerms:
    fields: dict[str, object] = {
        "requests_per_minute": 30,
        "concurrent_requests": 2,
        "retry_backoff_sec": 5,
        "max_retries": 3,
        "queue_depth": 100,
    }
    fields.update(over)
    return RateLimiterTerms(**fields)  # type: ignore[arg-type]


def config(**over: object) -> NegotiatedConfig:
    fields: dict[str, object] = {
        "schema_version": "mars777-1",
        "agreed_between": ("MaRs-777", "GROUP-XY"),
        "board_and_agents": board(),
        "world": world(),
        "movement_and_barriers": movement(),
        "scoring": scoring(),
        "pheromones": pheromones(),
        "network_and_league": league(),
        "rate_limiter_gatekeeper": rate_limiter(),
    }
    fields.update(over)
    return NegotiatedConfig(**fields)  # type: ignore[arg-type]
