"""TeamDeclaration composition and its structural refusals."""

import dataclasses

import pytest
from pregame_builders import COMMIT, hardware, team

from mars777_police.app.team_declaration_values import InvalidTeamDeclarationError


def test_valid_team_declaration() -> None:
    value = team()
    assert value.github_commit.value == COMMIT
    assert value.members == ("id-1001",)


def test_team_declaration_is_immutable() -> None:
    with pytest.raises(dataclasses.FrozenInstanceError):
        team().group_id = "other"  # type: ignore[misc]


@pytest.mark.parametrize("field", ["group_id", "group_name", "mcp_endpoint", "llm_model"])
@pytest.mark.parametrize("bad", [None, 1, ""])
def test_identity_fields_require_non_empty_str(field: str, bad: object) -> None:
    with pytest.raises(InvalidTeamDeclarationError):
        team(**{field: bad})


def test_code_version_requires_non_empty_str() -> None:
    with pytest.raises(InvalidTeamDeclarationError):
        team(code_version="")


@pytest.mark.parametrize("bad", [["id"], None, "id"])
def test_members_must_be_a_tuple(bad: object) -> None:
    with pytest.raises(InvalidTeamDeclarationError, match="members must be a tuple"):
        team(members=bad)


def test_members_must_be_non_empty() -> None:
    with pytest.raises(InvalidTeamDeclarationError, match="at least one member"):
        team(members=())


@pytest.mark.parametrize("bad", [(1,), ("",)])
def test_members_entries_must_be_non_empty_str(bad: tuple[object, ...]) -> None:
    with pytest.raises(InvalidTeamDeclarationError):
        team(members=bad)


def test_repos_must_be_repository_links() -> None:
    with pytest.raises(InvalidTeamDeclarationError, match="repos must be a RepositoryLinks"):
        team(repos={"police": "p", "thief": "t"})


def test_hardware_must_be_hardware_declaration() -> None:
    with pytest.raises(InvalidTeamDeclarationError, match="hardware must be a"):
        team(hardware={"os": "Linux"})


def test_github_commit_must_be_the_shared_primitive() -> None:
    with pytest.raises(InvalidTeamDeclarationError, match="github_commit must be a GitCommitSha"):
        team(github_commit=COMMIT)


def test_hardware_value_is_reused_not_copied() -> None:
    card = hardware()
    assert team(hardware=card).hardware is card
