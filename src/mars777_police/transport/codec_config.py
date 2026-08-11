"""Codec between the config wire DTO and the frozen 35-member semantic core.

Decoding is where JSON arrays become tuples and canonical decimal text becomes
`Decimal` - **at the transport boundary and nowhere else**. The semantic
constructors stay exactly as strict as they were: this module hands them
already-correct types rather than persuading them to accept wire ones.
"""

from ..domain.board import Position
from ..domain.config_league_sections import (
    NetworkAndLeagueTerms,
    PheromoneTerms,
    RateLimiterTerms,
)
from ..domain.config_sections import (
    BoardAndAgentsTerms,
    MovementAndBarrierTerms,
    ScoringTerms,
    WorldTerms,
)
from ..domain.negotiated_config import NegotiatedConfig
from .wire_config import NegotiatedConfigWire
from .wire_config_sections import (
    BoardAndAgentsWire,
    MovementAndBarriersWire,
    NetworkAndLeagueWire,
    PheromonesWire,
    RateLimiterWire,
    ScoringWire,
    WorldWire,
)
from .wire_scalars import decimal_from_text, text_from_decimal


def decode_config(wire: NegotiatedConfigWire) -> NegotiatedConfig:
    """Rebuild the 35-member binding core, decimals straight from their text."""
    board, world = wire.board_and_agents, wire.world
    movement, scoring = wire.movement_and_barriers, wire.scoring
    pheromones, network = wire.pheromones, wire.network_and_league
    limiter = wire.rate_limiter_gatekeeper
    return NegotiatedConfig(
        wire.schema_version,
        (wire.agreed_between[0], wire.agreed_between[1]),
        BoardAndAgentsTerms(
            board.grid_size,
            board.num_agents,
            Position(board.thief_start[0], board.thief_start[1]),
            Position(board.cop_start[0], board.cop_start[1]),
            board.axis_origin_corner,
            board.axis_start_index,
        ),
        WorldTerms(world.map_area, world.hint_max_words),
        MovementAndBarrierTerms(
            tuple(movement.move_set),
            movement.max_barriers,
            movement.max_moves,
            movement.survival_threshold,
        ),
        ScoringTerms(
            scoring.capture_cop,
            scoring.capture_thief,
            scoring.survival_cop,
            scoring.survival_thief,
            scoring.tie_score,
            scoring.technical_loss,
        ),
        PheromoneTerms(
            decimal_from_text(pheromones.pheromone_center_intensity),
            decimal_from_text(pheromones.pheromone_decay),
            pheromones.pheromone_grid_size,
        ),
        NetworkAndLeagueTerms(
            network.response_timeout_sec,
            network.watchdog_timeout_sec,
            network.num_games,
            network.diversity_reward,
            network.min_games_to_pass,
            network.max_games_per_team,
            network.token_budget_per_series,
        ),
        RateLimiterTerms(
            limiter.requests_per_minute,
            limiter.concurrent_requests,
            limiter.retry_backoff_sec,
            limiter.max_retries,
            limiter.queue_depth,
        ),
    )


def encode_config(config: NegotiatedConfig) -> NegotiatedConfigWire:
    """Render the core; decimals become canonical text, positions become arrays."""
    board, world = config.board_and_agents, config.world
    movement, scoring = config.movement_and_barriers, config.scoring
    pheromones, network = config.pheromones, config.network_and_league
    limiter = config.rate_limiter_gatekeeper
    return NegotiatedConfigWire(
        schema_version=config.schema_version,
        agreed_between=list(config.agreed_between),
        board_and_agents=BoardAndAgentsWire(
            grid_size=board.grid_size,
            num_agents=board.num_agents,
            thief_start=[board.thief_start.row, board.thief_start.col],
            cop_start=[board.cop_start.row, board.cop_start.col],
            axis_origin_corner=board.axis_origin_corner,
            axis_start_index=board.axis_start_index,
        ),
        world=WorldWire(map_area=world.map_area, hint_max_words=world.hint_max_words),
        movement_and_barriers=MovementAndBarriersWire(
            move_set=list(movement.move_set),
            max_barriers=movement.max_barriers,
            max_moves=movement.max_moves,
            survival_threshold=movement.survival_threshold,
        ),
        scoring=ScoringWire(
            capture_cop=scoring.capture_cop,
            capture_thief=scoring.capture_thief,
            survival_cop=scoring.survival_cop,
            survival_thief=scoring.survival_thief,
            tie_score=scoring.tie_score,
            technical_loss=scoring.technical_loss,
        ),
        pheromones=PheromonesWire(
            pheromone_center_intensity=text_from_decimal(pheromones.pheromone_center_intensity),
            pheromone_decay=text_from_decimal(pheromones.pheromone_decay),
            pheromone_grid_size=pheromones.pheromone_grid_size,
        ),
        network_and_league=NetworkAndLeagueWire(
            response_timeout_sec=network.response_timeout_sec,
            watchdog_timeout_sec=network.watchdog_timeout_sec,
            num_games=network.num_games,
            diversity_reward=network.diversity_reward,
            min_games_to_pass=network.min_games_to_pass,
            max_games_per_team=network.max_games_per_team,
            token_budget_per_series=network.token_budget_per_series,
        ),
        rate_limiter_gatekeeper=RateLimiterWire(
            requests_per_minute=limiter.requests_per_minute,
            concurrent_requests=limiter.concurrent_requests,
            retry_backoff_sec=limiter.retry_backoff_sec,
            max_retries=limiter.max_retries,
            queue_depth=limiter.queue_depth,
        ),
    )
