"""The complete binding config core as one typed immutable value.

**35 members**: ``schema_version`` and ``agreed_between`` at the top level plus
the 33 Appendix-B value keys across the seven frozen sections. Nothing outside
that core appears here - ``config_sha256`` and ``config_auth`` belong to the lock
evidence, not to the agreed physics.

This value validates **one proposed configuration**, including whether this build
supports its `schema_version` at all - `config_schema` owns that question, and a
configuration this code cannot represent is therefore not a value it constructs.
Byte-identity with the opponent, counter-proposal cadence and the token-budget
lifecycle are all LIVE concerns owned by the application layer.
"""

from dataclasses import dataclass

from .config_league_sections import NetworkAndLeagueTerms, PheromoneTerms, RateLimiterTerms
from .config_schema import require_supported_schema_version
from .config_sections import (
    BoardAndAgentsTerms,
    InvalidConfigSectionError,
    MovementAndBarrierTerms,
    ScoringTerms,
    WorldTerms,
)

AGREED_BETWEEN_SIZE = 2


@dataclass(frozen=True, slots=True)
class NegotiatedConfig:
    """The agreed physics and scoring contract for one sub-game."""

    schema_version: str
    agreed_between: tuple[str, str]
    board_and_agents: BoardAndAgentsTerms
    world: WorldTerms
    movement_and_barriers: MovementAndBarrierTerms
    scoring: ScoringTerms
    pheromones: PheromoneTerms
    network_and_league: NetworkAndLeagueTerms
    rate_limiter_gatekeeper: RateLimiterTerms

    def __post_init__(self) -> None:
        require_supported_schema_version(self.schema_version)
        if type(self.agreed_between) is not tuple:
            raise InvalidConfigSectionError(
                f"agreed_between must be a tuple, got {type(self.agreed_between).__name__}",
            )
        if len(self.agreed_between) != AGREED_BETWEEN_SIZE:
            raise InvalidConfigSectionError(
                f"agreed_between must name exactly {AGREED_BETWEEN_SIZE} participants,"
                f" got {len(self.agreed_between)}",
            )
        for group_id in self.agreed_between:
            if type(group_id) is not str or not group_id:
                raise InvalidConfigSectionError("agreed_between entries must be non-empty str")
        for name, expected in (
            ("board_and_agents", BoardAndAgentsTerms),
            ("world", WorldTerms),
            ("movement_and_barriers", MovementAndBarrierTerms),
            ("scoring", ScoringTerms),
            ("pheromones", PheromoneTerms),
            ("network_and_league", NetworkAndLeagueTerms),
            ("rate_limiter_gatekeeper", RateLimiterTerms),
        ):
            value = getattr(self, name)
            if type(value) is not expected:
                raise InvalidConfigSectionError(
                    f"{name} must be a {expected.__name__}, got {type(value).__name__}",
                )
