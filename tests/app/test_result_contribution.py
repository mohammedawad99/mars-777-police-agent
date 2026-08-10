"""ResultContribution: six ordered entries under one game-fixed commit."""

import dataclasses

import pytest
from result_builders import COMMIT_A, COMMIT_B, contribution, entries, entry

from mars777_police.app.result_values import InvalidResultValueError, ResultContribution


def test_valid_contribution() -> None:
    value = contribution()
    assert value.group_id == "MaRs-777"
    assert len(value.entries) == 6


def test_contribution_field_order() -> None:
    assert [f.name for f in dataclasses.fields(ResultContribution)] == ["group_id", "entries"]


def test_contribution_carries_no_derived_or_joint_member() -> None:
    names = {f.name for f in dataclasses.fields(ResultContribution)}
    assert not names & {
        "total_tokens",
        "cumulative",
        "timestamp",
        "github_links",
        "declaration_ref",
        "scores",
    }


@pytest.mark.parametrize("bad", [None, 1, True])
def test_group_id_must_be_a_str(bad: object) -> None:
    with pytest.raises(InvalidResultValueError, match="group_id must be a str"):
        contribution(group_id=bad)


def test_group_id_must_be_non_empty() -> None:
    with pytest.raises(InvalidResultValueError, match="group_id must be non-empty"):
        contribution(group_id="")


def test_entries_must_be_a_tuple_not_a_list() -> None:
    with pytest.raises(InvalidResultValueError, match="entries must be a tuple"):
        contribution(entries=list(entries()))


def test_entries_must_hold_entry_values() -> None:
    with pytest.raises(InvalidResultValueError, match="entry must be a ResultContributionEntry"):
        contribution(entries=({"sub_game": 1},) * 6)


@pytest.mark.parametrize(
    "bad",
    [
        entries()[:5],
        (*entries(), entry(6, COMMIT_A, 60)),
        (entry(1), entry(1), entry(3), entry(4), entry(5), entry(6)),
        (entry(1), entry(2), entry(4), entry(5), entry(6), entry(6)),
        (entry(2), entry(1), entry(3), entry(4), entry(5), entry(6)),
        (),
    ],
)
def test_entries_must_cover_one_through_six_exactly_once_ascending(bad: tuple[object, ...]) -> None:
    with pytest.raises(InvalidResultValueError, match="must cover sub-games"):
        contribution(entries=bad)


def test_the_six_commits_must_be_identical() -> None:
    mixed = (*entries()[:5], entry(6, COMMIT_B, 60))
    with pytest.raises(InvalidResultValueError, match="same github_commit"):
        contribution(entries=mixed)


def test_token_counts_may_differ_per_sub_game() -> None:
    value = contribution()
    assert [e.tokens for e in value.entries] == [10, 20, 30, 40, 50, 60]


def test_contribution_is_immutable() -> None:
    with pytest.raises(dataclasses.FrozenInstanceError):
        contribution().group_id = "other"  # type: ignore[misc]
