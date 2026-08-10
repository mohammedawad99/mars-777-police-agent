"""The 35-member binding config core and the eleven-profile projection.

Mapping only - this module produces JSON-native material and never hashes,
authenticates or locks anything. It is separated from `protocol.config_lock` by
measured line budget and by responsibility: the two Appendix-B tables are a
*structure*, while the digest, the lock context and the proof are a *protocol*.

Every member is mapped **explicitly** from the frozen section tables below. A
member added to a `NegotiatedConfig` section tomorrow does not silently enter the
hashed bytes, and a member removed from the table stops being hashed loudly
rather than quietly.
"""

from typing import Final

from ..app.interop_profiles import InteropProfileSet
from ..domain.board import Position
from ..domain.negotiated_config import NegotiatedConfig

CONFIG_CORE_MEMBERS: Final[int] = 35
"""`schema_version` + `agreed_between` + the 33 Appendix-B value keys."""

_SECTIONS: Final[tuple[tuple[str, tuple[str, ...]], ...]] = (
    (
        "board_and_agents",
        (
            "grid_size",
            "num_agents",
            "thief_start",
            "cop_start",
            "axis_origin_corner",
            "axis_start_index",
        ),
    ),
    ("world", ("map_area", "hint_max_words")),
    ("movement_and_barriers", ("move_set", "max_barriers", "max_moves", "survival_threshold")),
    (
        "scoring",
        (
            "capture_cop",
            "capture_thief",
            "survival_cop",
            "survival_thief",
            "tie_score",
            "technical_loss",
        ),
    ),
    ("pheromones", ("pheromone_center_intensity", "pheromone_decay", "pheromone_grid_size")),
    (
        "network_and_league",
        (
            "response_timeout_sec",
            "watchdog_timeout_sec",
            "num_games",
            "diversity_reward",
            "min_games_to_pass",
            "max_games_per_team",
            "token_budget_per_series",
        ),
    ),
    (
        "rate_limiter_gatekeeper",
        (
            "requests_per_minute",
            "concurrent_requests",
            "retry_backoff_sec",
            "max_retries",
            "queue_depth",
        ),
    ),
)
"""The seven Appendix-B sections and their exact field names, in contract order."""

PROFILE_MEMBERS: Final[tuple[str, ...]] = (
    "series_convention",
    "auth_profile",
    "key_id",
    "commitment_codec",
    "result_profile",
    "compatibility_profile",
    "tool_name_profile",
    "canonicalization_profile",
    "sealed_record_profile",
    "state_representation_profile",
    "nonce_representation_profile",
)
"""The eleven series-wide values the lock context binds cryptographically."""


def _value(item: object) -> object:
    """Map one already-valid config member to its JSON-native form.

    Exact types only: a `Position` becomes the `[row, col]` array JDEC-012
    locks, `move_set` becomes an order-significant array, and every other member
    is already `str`, `int` or `Decimal` and passes through untouched.
    """
    if type(item) is Position:
        return [item.row, item.col]
    if type(item) is tuple:
        return list(item)
    return item


def config_core(config: NegotiatedConfig) -> dict[str, object]:
    """Return the exact 35-member binding config core."""
    core: dict[str, object] = {
        "schema_version": config.schema_version,
        "agreed_between": list(config.agreed_between),
    }
    for section, fields in _SECTIONS:
        terms = getattr(config, section)
        core[section] = {field: _value(getattr(terms, field)) for field in fields}
    return core


def profiles_core(profiles: InteropProfileSet) -> dict[str, object]:
    """Return the eleven profile tokens, each serialized exactly as its identifier."""
    return {name: getattr(profiles, name).value for name in PROFILE_MEMBERS}
