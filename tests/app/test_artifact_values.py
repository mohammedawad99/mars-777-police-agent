"""Shared cross-artifact primitives: exact representations, no coercion."""

import dataclasses

import pytest

from mars777_police.app.artifact_values import (
    GitCommitSha,
    InvalidGitCommitShaError,
    InvalidUtcTimestampError,
    UtcTimestamp,
)

VALID_SHA = "2113e68d141ab087b849f83a7d91d66620e8ad85"
VALID_TS = "2026-08-07T00:00:00Z"


def test_valid_commit_round_trips() -> None:
    assert GitCommitSha(VALID_SHA).value == VALID_SHA


def test_commit_equality_and_immutability() -> None:
    assert GitCommitSha(VALID_SHA) == GitCommitSha(VALID_SHA)
    with pytest.raises(dataclasses.FrozenInstanceError):
        GitCommitSha(VALID_SHA).value = VALID_SHA  # type: ignore[misc]


@pytest.mark.parametrize("bad", [None, 40, b"a" * 40, True])
def test_commit_rejects_non_str(bad: object) -> None:
    with pytest.raises(InvalidGitCommitShaError, match="must be a str"):
        GitCommitSha(bad)  # type: ignore[arg-type]


@pytest.mark.parametrize("bad", ["a" * 39, "a" * 41, "", VALID_SHA + " "])
def test_commit_rejects_wrong_length(bad: str) -> None:
    with pytest.raises(InvalidGitCommitShaError, match="exactly 40"):
        GitCommitSha(bad)


@pytest.mark.parametrize("bad", [VALID_SHA.upper(), "g" * 40, "0x" + "a" * 38, " " + "a" * 39])
def test_commit_rejects_non_lower_hex(bad: str) -> None:
    with pytest.raises(InvalidGitCommitShaError, match="lowercase hexadecimal"):
        GitCommitSha(bad)


def test_valid_timestamp_round_trips() -> None:
    assert UtcTimestamp(VALID_TS).value == VALID_TS


def test_timestamp_equality_and_immutability() -> None:
    assert UtcTimestamp(VALID_TS) == UtcTimestamp(VALID_TS)
    with pytest.raises(dataclasses.FrozenInstanceError):
        UtcTimestamp(VALID_TS).value = VALID_TS  # type: ignore[misc]


@pytest.mark.parametrize("bad", [None, 20, b"x" * 20])
def test_timestamp_rejects_non_str(bad: object) -> None:
    with pytest.raises(InvalidUtcTimestampError, match="must be a str"):
        UtcTimestamp(bad)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "bad",
    ["2026-08-07T00:00:00", "2026-08-07T00:00:00.000Z", "2026-08-07T00:00:00+00:00", ""],
)
def test_timestamp_rejects_wrong_length(bad: str) -> None:
    with pytest.raises(InvalidUtcTimestampError, match="exactly 20"):
        UtcTimestamp(bad)


@pytest.mark.parametrize(
    "bad",
    [
        "2026/08-07T00:00:00Z",
        "2026-08/07T00:00:00Z",
        "2026-08-07 00:00:00Z",
        "2026-08-07T00-00:00Z",
        "2026-08-07T00:00-00Z",
        "2026-08-07T00:00:00z",
    ],
)
def test_timestamp_rejects_wrong_literal(bad: str) -> None:
    with pytest.raises(InvalidUtcTimestampError, match="lexical form"):
        UtcTimestamp(bad)


@pytest.mark.parametrize("bad", ["20x6-08-07T00:00:00Z", "2026-08-07T0 :00:00Z"])
def test_timestamp_rejects_non_digits(bad: str) -> None:
    with pytest.raises(InvalidUtcTimestampError, match="ASCII digits"):
        UtcTimestamp(bad)
