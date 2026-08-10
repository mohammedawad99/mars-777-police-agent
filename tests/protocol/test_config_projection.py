"""The binding config core: exactly 35 members, and byte-exact decimals.

`config_sha256` is what two peers compare before they agree to play, so the
projection is walked and counted here rather than trusted, and the digest is
proved to move when any one member moves.
"""

from dataclasses import replace
from decimal import Decimal

from r16_builders import PROFILES, config

from mars777_police.domain.config_league_sections import PheromoneTerms
from mars777_police.domain.config_sections import WorldTerms
from mars777_police.protocol.canonical import canonical_json_bytes
from mars777_police.protocol.config_lock import config_sha256
from mars777_police.protocol.config_projection import (
    CONFIG_CORE_MEMBERS,
    config_core,
    profiles_core,
)

SECTION_SIZES = {
    "board_and_agents": 6,
    "world": 2,
    "movement_and_barriers": 4,
    "scoring": 6,
    "pheromones": 3,
    "network_and_league": 7,
    "rate_limiter_gatekeeper": 5,
}


def test_the_core_carries_exactly_thirty_five_members() -> None:
    core = config_core(config())
    counted = 2 + sum(len(core[section]) for section in SECTION_SIZES)  # type: ignore[arg-type]
    assert counted == CONFIG_CORE_MEMBERS == 35


def test_each_section_carries_its_frozen_field_count() -> None:
    core = config_core(config())
    for section, size in SECTION_SIZES.items():
        assert len(core[section]) == size, section  # type: ignore[arg-type]
    assert set(core) == {"schema_version", "agreed_between", *SECTION_SIZES}


def test_the_two_fixed_decimals_are_emitted_verbatim() -> None:
    raw = canonical_json_bytes(config_core(config()))
    assert b'"pheromone_center_intensity":0.9' in raw
    assert b'"pheromone_decay":0.10' in raw
    assert b"0.1," not in raw


def test_positions_become_the_locked_coordinate_arrays() -> None:
    core = config_core(config())
    board = core["board_and_agents"]
    assert isinstance(board, dict)
    assert board["thief_start"] == [3, 3]
    assert board["cop_start"] == [0, 0]


def test_the_move_set_stays_an_order_significant_array() -> None:
    core = config_core(config())
    movement = core["movement_and_barriers"]
    assert isinstance(movement, dict)
    assert movement["move_set"] == ["N", "S", "E", "W", "STAY"]


def test_nothing_outside_the_core_leaks_into_the_hashed_bytes() -> None:
    raw = canonical_json_bytes(config_core(config()))
    for forbidden in (b"config_sha256", b"config_auth", b"auth_tag", b"sub_game", b"profiles"):
        assert forbidden not in raw


def test_the_digest_is_deterministic() -> None:
    assert config_sha256(config()) == config_sha256(config())
    assert len(config_sha256(config()).value) == 64


def test_changing_one_negotiable_value_changes_the_digest() -> None:
    other = replace(config(), world=WorldTerms("New York", 16))
    assert config_sha256(other) != config_sha256(config())


def test_a_decimal_that_differs_only_in_trailing_zeros_changes_the_digest() -> None:
    """`0.1` and `0.10` are the same number and deliberately not the same config."""
    other = replace(config(), pheromones=PheromoneTerms(Decimal("0.9"), Decimal("0.1"), 5))
    assert config_sha256(other) != config_sha256(config())


def test_the_profile_projection_carries_the_eleven_series_wide_tokens() -> None:
    projected = profiles_core(PROFILES)
    assert len(projected) == 11
    assert projected["auth_profile"] == "HMAC_SHA256"
    assert projected["key_id"] == "mars777-k1"
    assert projected["canonicalization_profile"] == "CANONICAL_JSON_V1"
    assert projected["series_convention"] == "FIXED_ROLE"
