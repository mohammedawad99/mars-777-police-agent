"""Wire DTOs for the seven Appendix-B config sections.

Split from `wire_config` by the same line that splits the semantic sections: the
physics tables here, the composite and the profile set there. Every model is
`extra="forbid"` and `strict=True`, so an unknown member, a string where an int
belongs, or a `bool` standing in for an `int` is refused by the published schema
rather than by a constructor three layers down.

The two pheromone decimals are `DecimalText`, never JSON numbers - see
`wire_scalars`.
"""

from pydantic import BaseModel, ConfigDict

from .wire_scalars import DecimalText, NonEmptyText

WIRE = ConfigDict(extra="forbid", strict=True)


class BoardAndAgentsWire(BaseModel):
    """App F Table 13. Positions cross as two-integer arrays (JDEC-012)."""

    model_config = WIRE

    grid_size: int
    num_agents: int
    thief_start: list[int]
    cop_start: list[int]
    axis_origin_corner: NonEmptyText
    axis_start_index: int


class WorldWire(BaseModel):
    """App F Table 14. `map_area` may be empty, meaning generic."""

    model_config = WIRE

    map_area: str
    hint_max_words: int


class MovementAndBarriersWire(BaseModel):
    """App F Table 15. `move_set` is order-significant."""

    model_config = WIRE

    move_set: list[str]
    max_barriers: int
    max_moves: int
    survival_threshold: int


class ScoringWire(BaseModel):
    """App F Table 17 plus the Ch 3 / App E #48 technical loss (C-07)."""

    model_config = WIRE

    capture_cop: int
    capture_thief: int
    survival_cop: int
    survival_thief: int
    tie_score: int
    technical_loss: int


class PheromonesWire(BaseModel):
    """App F Table 16. The two FIXED decimals cross as canonical text."""

    model_config = WIRE

    pheromone_center_intensity: DecimalText
    pheromone_decay: DecimalText
    pheromone_grid_size: int


class NetworkAndLeagueWire(BaseModel):
    """App F Table 18 with the two Table-19 timeouts."""

    model_config = WIRE

    response_timeout_sec: int
    watchdog_timeout_sec: int
    num_games: int
    diversity_reward: int
    min_games_to_pass: int
    max_games_per_team: int
    token_budget_per_series: int


class RateLimiterWire(BaseModel):
    """App F Table 19 rows 1-5."""

    model_config = WIRE

    requests_per_minute: int
    concurrent_requests: int
    retry_backoff_sec: int
    max_retries: int
    queue_depth: int
