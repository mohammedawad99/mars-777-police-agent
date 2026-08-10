"""ResultContributionEntry: one sender-owned sub-game record."""

import dataclasses
from decimal import Decimal

import pytest
from result_builders import COMMIT_A, entry

from mars777_police.app.result_values import InvalidResultValueError, ResultContributionEntry


def test_valid_entry_at_each_end_of_the_series() -> None:
    assert entry(1).sub_game == 1
    assert entry(6).sub_game == 6


def test_entry_field_order() -> None:
    assert [f.name for f in dataclasses.fields(ResultContributionEntry)] == [
        "sub_game",
        "github_commit",
        "tokens",
    ]


def test_entry_carries_no_score_or_identity_member() -> None:
    names = {f.name for f in dataclasses.fields(ResultContributionEntry)}
    assert not names & {"cop_score", "thief_score", "outcome", "timestamp", "group_id", "digest"}


@pytest.mark.parametrize("bad", [0, 7, -1])
def test_entry_rejects_out_of_range_sub_game(bad: int) -> None:
    with pytest.raises(InvalidResultValueError, match="sub_game must be within"):
        entry(bad)


@pytest.mark.parametrize("bad", [True, "1", 1.0, Decimal(1), None])
def test_entry_sub_game_is_a_strict_int(bad: object) -> None:
    with pytest.raises(InvalidResultValueError, match="sub_game must be an int"):
        ResultContributionEntry(bad, entry().github_commit, 0)  # type: ignore[arg-type]


def test_entry_rejects_raw_commit_string() -> None:
    with pytest.raises(InvalidResultValueError, match="github_commit must be a GitCommitSha"):
        ResultContributionEntry(1, COMMIT_A, 0)  # type: ignore[arg-type]


@pytest.mark.parametrize("bad", [True, "0", 0.0, Decimal(0), None])
def test_entry_tokens_is_a_strict_int(bad: object) -> None:
    with pytest.raises(InvalidResultValueError, match="tokens must be an int"):
        entry(tokens=bad)  # type: ignore[arg-type]


def test_entry_rejects_negative_tokens() -> None:
    with pytest.raises(InvalidResultValueError, match="tokens must be >= 0"):
        entry(tokens=-1)


def test_zero_tokens_is_valid() -> None:
    assert entry(tokens=0).tokens == 0


def test_entry_is_immutable() -> None:
    with pytest.raises(dataclasses.FrozenInstanceError):
        entry().tokens = 5  # type: ignore[misc]
