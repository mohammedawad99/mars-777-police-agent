"""The three league-side Appendix-B config sections as typed value objects.

Split from ``domain.config_sections`` by measured line budget and semantic
ownership: pheromone physics, league/network terms and the rate-limiter
gatekeeper. ``ScentParams`` and ``SeriesConfig`` already exist in
``domain.config_model`` and are reused rather than re-specified, so no value is
represented twice.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Final

from .config_model import ScentParams, SeriesConfig
from .config_sections import InvalidConfigSectionError, require_at_least
from .errors import require_int

FIXED_DIVERSITY_REWARD: Final[int] = 10
FIXED_MIN_GAMES_TO_PASS: Final[int] = 2
FIXED_MAX_GAMES_PER_TEAM: Final[int] = 10
MIN_REQUESTS_PER_MINUTE: Final[int] = 30
MIN_CONCURRENT_REQUESTS: Final[int] = 2
MIN_RETRY_BACKOFF_SEC: Final[int] = 5
MIN_MAX_RETRIES: Final[int] = 3
MIN_QUEUE_DEPTH: Final[int] = 100


@dataclass(frozen=True, slots=True)
class PheromoneTerms:
    """App F Table 16, all three FIXED. Validation is delegated to ``ScentParams``."""

    pheromone_center_intensity: Decimal
    pheromone_decay: Decimal
    pheromone_grid_size: int

    def __post_init__(self) -> None:
        ScentParams(
            self.pheromone_center_intensity,
            self.pheromone_decay,
            self.pheromone_grid_size,
        )


@dataclass(frozen=True, slots=True)
class NetworkAndLeagueTerms:
    """App F Table 18 with the two Table-19 timeouts.

    ``num_games`` is validated by the existing ``SeriesConfig``, which owns the
    FIXED-6 rule; ``token_budget_per_series`` is stored and range-checked only -
    its PRE-STEP0-AGREED lifecycle is an application concern, not a value rule.
    """

    response_timeout_sec: int
    watchdog_timeout_sec: int
    num_games: int
    diversity_reward: int
    min_games_to_pass: int
    max_games_per_team: int
    token_budget_per_series: int

    def __post_init__(self) -> None:
        require_at_least(self.response_timeout_sec, "response_timeout_sec", 1)
        require_at_least(self.watchdog_timeout_sec, "watchdog_timeout_sec", 1)
        SeriesConfig(self.num_games)
        for name, locked in (
            ("diversity_reward", FIXED_DIVERSITY_REWARD),
            ("min_games_to_pass", FIXED_MIN_GAMES_TO_PASS),
            ("max_games_per_team", FIXED_MAX_GAMES_PER_TEAM),
        ):
            value = require_int(getattr(self, name), name, InvalidConfigSectionError)
            if value != locked:
                raise InvalidConfigSectionError(f"{name} is FIXED at {locked}, got {value}")
        require_at_least(self.token_budget_per_series, "token_budget_per_series", 1)


@dataclass(frozen=True, slots=True)
class RateLimiterTerms:
    """App F Table 19 rows 1-5, all MINIMUM floors."""

    requests_per_minute: int
    concurrent_requests: int
    retry_backoff_sec: int
    max_retries: int
    queue_depth: int

    def __post_init__(self) -> None:
        for name, floor in (
            ("requests_per_minute", MIN_REQUESTS_PER_MINUTE),
            ("concurrent_requests", MIN_CONCURRENT_REQUESTS),
            ("retry_backoff_sec", MIN_RETRY_BACKOFF_SEC),
            ("max_retries", MIN_MAX_RETRIES),
            ("queue_depth", MIN_QUEUE_DEPTH),
        ):
            require_at_least(getattr(self, name), name, floor)
