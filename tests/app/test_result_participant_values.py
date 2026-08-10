"""The participant-scoped pair values the shared result core holds."""

import dataclasses
from decimal import Decimal

import pytest
from result_builders import COMMIT_A, COMMIT_B

from mars777_police.app.artifact_values import GitCommitSha
from mars777_police.app.result_values import (
    InvalidResultValueError,
    ParticipantGitCommits,
    ParticipantTokenUsage,
)


def test_valid_commit_pair() -> None:
    pair = ParticipantGitCommits(GitCommitSha(COMMIT_A), GitCommitSha(COMMIT_B))
    assert pair.group_a.value == COMMIT_A
    assert pair.group_b.value == COMMIT_B


def test_commit_pair_field_order_and_equality() -> None:
    assert [f.name for f in dataclasses.fields(ParticipantGitCommits)] == ["group_a", "group_b"]
    left = ParticipantGitCommits(GitCommitSha(COMMIT_A), GitCommitSha(COMMIT_B))
    assert left == ParticipantGitCommits(GitCommitSha(COMMIT_A), GitCommitSha(COMMIT_B))


def test_commit_pair_is_immutable() -> None:
    pair = ParticipantGitCommits(GitCommitSha(COMMIT_A), GitCommitSha(COMMIT_B))
    with pytest.raises(dataclasses.FrozenInstanceError):
        pair.group_a = GitCommitSha(COMMIT_B)  # type: ignore[misc]


@pytest.mark.parametrize("slot", ["group_a", "group_b"])
def test_commit_pair_rejects_raw_hex_string(slot: str) -> None:
    fields: dict[str, object] = {
        "group_a": GitCommitSha(COMMIT_A),
        "group_b": GitCommitSha(COMMIT_B),
        slot: COMMIT_A,
    }
    with pytest.raises(InvalidResultValueError, match=f"{slot} must be a GitCommitSha"):
        ParticipantGitCommits(**fields)  # type: ignore[arg-type]


def test_valid_token_pair_including_zero() -> None:
    pair = ParticipantTokenUsage(0, 200000)
    assert (pair.group_a, pair.group_b) == (0, 200000)


def test_token_pair_field_order_and_immutability() -> None:
    assert [f.name for f in dataclasses.fields(ParticipantTokenUsage)] == ["group_a", "group_b"]
    with pytest.raises(dataclasses.FrozenInstanceError):
        ParticipantTokenUsage(0, 0).group_a = 1  # type: ignore[misc]


@pytest.mark.parametrize("slot", ["group_a", "group_b"])
@pytest.mark.parametrize("bad", [True, False, "5", 5.0, Decimal(5), None])
def test_token_pair_rejects_non_int(slot: str, bad: object) -> None:
    fields: dict[str, object] = {"group_a": 0, "group_b": 0, slot: bad}
    with pytest.raises(InvalidResultValueError, match=f"{slot} must be an int"):
        ParticipantTokenUsage(**fields)  # type: ignore[arg-type]


@pytest.mark.parametrize("slot", ["group_a", "group_b"])
def test_token_pair_rejects_negative(slot: str) -> None:
    fields: dict[str, object] = {"group_a": 0, "group_b": 0, slot: -1}
    with pytest.raises(InvalidResultValueError, match=f"{slot} must be >= 0"):
        ParticipantTokenUsage(**fields)  # type: ignore[arg-type]


def test_no_combined_total_member_exists() -> None:
    names = {f.name for f in dataclasses.fields(ParticipantTokenUsage)}
    assert not names & {"total", "combined", "police", "thief"}
