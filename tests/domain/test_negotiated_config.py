"""NegotiatedConfig: the complete 35-member binding core."""

import dataclasses

import pytest
from config_builders import config

from mars777_police.domain.config_sections import InvalidConfigSectionError
from mars777_police.domain.negotiated_config import NegotiatedConfig

SECTION_SIZES = {
    "board_and_agents": 6,
    "world": 2,
    "movement_and_barriers": 4,
    "scoring": 6,
    "pheromones": 3,
    "network_and_league": 7,
    "rate_limiter_gatekeeper": 5,
}


def test_valid_full_construction() -> None:
    assert config().schema_version == "mars777-1"


def test_the_core_has_exactly_thirty_five_members() -> None:
    top_level = [f.name for f in dataclasses.fields(NegotiatedConfig)]
    assert len(top_level) == 9
    scalars = sum(len(dataclasses.fields(type(getattr(config(), name)))) for name in SECTION_SIZES)
    assert scalars == 33
    assert scalars + 2 == 35


def test_each_section_has_its_frozen_member_count() -> None:
    value = config()
    for name, size in SECTION_SIZES.items():
        assert len(dataclasses.fields(type(getattr(value, name)))) == size


def test_the_core_carries_no_digest_or_auth_member() -> None:
    names = {f.name for f in dataclasses.fields(NegotiatedConfig)}
    assert not names & {"config_sha256", "config_auth", "auth", "profiles"}


@pytest.mark.parametrize("bad", ["", None, 1])
def test_schema_version_must_be_non_empty_str(bad: object) -> None:
    with pytest.raises(InvalidConfigSectionError, match="schema_version"):
        config(schema_version=bad)


@pytest.mark.parametrize("bad", [["a", "b"], None, "ab"])
def test_agreed_between_must_be_a_tuple(bad: object) -> None:
    with pytest.raises(InvalidConfigSectionError, match="agreed_between must be a tuple"):
        config(agreed_between=bad)


@pytest.mark.parametrize("bad", [("a",), ("a", "b", "c"), ()])
def test_agreed_between_names_exactly_two_participants(bad: tuple[str, ...]) -> None:
    with pytest.raises(InvalidConfigSectionError, match="exactly 2 participants"):
        config(agreed_between=bad)


@pytest.mark.parametrize("bad", [("", "b"), (1, "b")])
def test_agreed_between_entries_must_be_non_empty_str(bad: tuple[object, ...]) -> None:
    with pytest.raises(InvalidConfigSectionError, match="non-empty str"):
        config(agreed_between=bad)


@pytest.mark.parametrize("field", list(SECTION_SIZES))
def test_every_section_must_be_its_own_type(field: str) -> None:
    with pytest.raises(InvalidConfigSectionError, match=f"{field} must be a"):
        config(**{field: {"nope": 1}})


def test_config_is_immutable() -> None:
    with pytest.raises(dataclasses.FrozenInstanceError):
        config().schema_version = "other"  # type: ignore[misc]
