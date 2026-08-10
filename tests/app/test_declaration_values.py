"""Declaration lifecycle: partial, merged and final immutable snapshots."""

import dataclasses

import pytest
from pregame_builders import END, START, declaration, team, times

from mars777_police.app.artifact_values import UtcTimestamp
from mars777_police.app.declaration_values import (
    Declaration,
    DeclarationTeams,
    DeclarationTimes,
    InvalidDeclarationError,
)


def test_times_accept_absent_game_end() -> None:
    assert times().game_end is None


def test_times_accept_present_game_end() -> None:
    assert times(END).game_end == UtcTimestamp(END)


def test_times_reject_raw_start() -> None:
    with pytest.raises(InvalidDeclarationError, match="game_start must be a UtcTimestamp"):
        DeclarationTimes(START, None)  # type: ignore[arg-type]


def test_times_reject_raw_end() -> None:
    with pytest.raises(InvalidDeclarationError, match="game_end must be a UtcTimestamp"):
        DeclarationTimes(UtcTimestamp(START), END)  # type: ignore[arg-type]


def test_partial_snapshot_with_only_group_a() -> None:
    teams = DeclarationTeams(team(), None)
    assert teams.is_merged is False


def test_partial_snapshot_with_only_group_b() -> None:
    teams = DeclarationTeams(None, team())
    assert teams.is_merged is False


def test_merged_snapshot_has_both_subtrees() -> None:
    assert DeclarationTeams(team(), team()).is_merged is True


def test_declaration_teams_reject_neither_present() -> None:
    with pytest.raises(InvalidDeclarationError, match="at least one participant"):
        DeclarationTeams(None, None)


@pytest.mark.parametrize("slot", ["group_a", "group_b"])
def test_declaration_teams_reject_raw_subtree(slot: str) -> None:
    kwargs: dict[str, object] = {"group_a": None, "group_b": None, slot: {"group_id": "x"}}
    with pytest.raises(InvalidDeclarationError, match="must be a TeamDeclaration"):
        DeclarationTeams(**kwargs)  # type: ignore[arg-type]


def test_valid_partial_declaration() -> None:
    assert declaration().teams.is_merged is False


def test_merged_declaration_may_carry_game_end() -> None:
    value = declaration(teams=DeclarationTeams(team(), team()), times=times(END))
    assert value.times.game_end == UtcTimestamp(END)


def test_merged_declaration_without_game_end_is_valid() -> None:
    assert declaration(teams=DeclarationTeams(team(), team())).times.game_end is None


def test_partial_declaration_cannot_carry_game_end() -> None:
    with pytest.raises(InvalidDeclarationError, match="only once both participant"):
        declaration(times=times(END))


@pytest.mark.parametrize("field", ["game_id", "game_uid"])
@pytest.mark.parametrize("bad", [None, 1])
def test_identity_must_be_str(field: str, bad: object) -> None:
    with pytest.raises(InvalidDeclarationError, match="must be a str"):
        declaration(**{field: bad})


@pytest.mark.parametrize("field", ["game_id", "game_uid"])
def test_identity_must_be_non_empty(field: str) -> None:
    with pytest.raises(InvalidDeclarationError, match="must be non-empty"):
        declaration(**{field: ""})


@pytest.mark.parametrize("bad", [True, "200000", 200000.0, None])
def test_token_budget_is_strict_int(bad: object) -> None:
    with pytest.raises(InvalidDeclarationError, match="token_budget_per_series must be an int"):
        declaration(token_budget_per_series=bad)


def test_token_budget_must_be_positive() -> None:
    with pytest.raises(InvalidDeclarationError, match="token_budget_per_series must be > 0"):
        declaration(token_budget_per_series=0)


def test_times_must_be_declaration_times() -> None:
    with pytest.raises(InvalidDeclarationError, match="times must be a DeclarationTimes"):
        declaration(times={"game_start": START})


def test_teams_must_be_declaration_teams() -> None:
    with pytest.raises(InvalidDeclarationError, match="teams must be a DeclarationTeams"):
        declaration(teams={"group_a": None})


def test_declaration_is_immutable() -> None:
    with pytest.raises(dataclasses.FrozenInstanceError):
        declaration().game_id = "other"  # type: ignore[misc]


def test_declaration_carries_no_auth_member() -> None:
    assert not any("auth" in field.name for field in dataclasses.fields(Declaration))
