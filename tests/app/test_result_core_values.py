"""The result approval core value types: structure only, and exactly the frozen set.

Everything checked here is checkable because it already sits inside one immutable
object. Whether a score is the one the played sub-game produced, whether a link
resolves and whether the participants really played are LIVE duties elsewhere.
"""

from dataclasses import FrozenInstanceError, fields

import pytest
from r16_builders import (
    COMMIT_A,
    COMMIT_B,
    CUMULATIVE,
    DECLARATION_REF,
    GAME_ID,
    GAME_UID,
    LINKS,
    PARTICIPANTS,
    STAMP,
)

from mars777_police.app.result_core_values import (
    CumulativeResult,
    ResultApprovalCore,
    SubGameResult,
)
from mars777_police.app.result_values import (
    InvalidResultValueError,
    ParticipantGitCommits,
    ParticipantTokenUsage,
)
from mars777_police.domain.terminal import Outcome

COMMITS = ParticipantGitCommits(COMMIT_A, COMMIT_B)
TOKENS = ParticipantTokenUsage(10, 20)
LINES = tuple(SubGameResult(i, 20, 5, Outcome.CAPTURE, COMMITS, TOKENS) for i in range(1, 7))


def core(**overrides: object) -> ResultApprovalCore:
    fields: dict[str, object] = {
        "game_id": GAME_ID,
        "game_uid": GAME_UID,
        "declaration_ref": DECLARATION_REF,
        "participants": PARTICIPANTS,
        "github_links": LINKS,
        "sub_games": LINES,
        "cumulative": CUMULATIVE,
        "total_tokens": TOKENS,
        "timestamp": STAMP,
    }
    fields.update(overrides)
    return ResultApprovalCore(**fields)  # type: ignore[arg-type]


def test_the_core_declares_exactly_the_frozen_members() -> None:
    assert tuple(f.name for f in fields(ResultApprovalCore)) == (
        "game_id",
        "game_uid",
        "declaration_ref",
        "participants",
        "github_links",
        "sub_games",
        "cumulative",
        "total_tokens",
        "timestamp",
    )


def test_the_excluded_members_are_not_fields_at_all() -> None:
    for absent in ("result_sha256", "mutual_agreement", "reported_by"):
        assert not hasattr(core(), absent)


def test_the_core_is_immutable() -> None:
    with pytest.raises(FrozenInstanceError):
        core().game_id = "other"


def test_exactly_six_ascending_sub_games_are_required() -> None:
    for bad in (LINES[:5], (*LINES, LINES[0]), LINES[::-1], ()):
        with pytest.raises(InvalidResultValueError):
            core(sub_games=bad)


def test_sub_games_must_be_a_tuple_of_lines() -> None:
    with pytest.raises(InvalidResultValueError):
        core(sub_games=list(LINES))
    with pytest.raises(InvalidResultValueError):
        core(sub_games=(1, 2, 3, 4, 5, 6))


@pytest.mark.parametrize("field", ["game_id", "game_uid", "declaration_ref"])
def test_identity_members_must_be_non_empty_strings(field: str) -> None:
    for bad in ("", None, 1):
        with pytest.raises(InvalidResultValueError):
            core(**{field: bad})


@pytest.mark.parametrize(
    "field", ["participants", "github_links", "cumulative", "total_tokens", "timestamp"]
)
def test_every_composite_member_is_exact_typed(field: str) -> None:
    with pytest.raises(InvalidResultValueError):
        core(**{field: "not the right type"})


def test_a_sub_game_line_refuses_a_raw_outcome_string() -> None:
    with pytest.raises(InvalidResultValueError):
        SubGameResult(1, 20, 5, "capture", COMMITS, TOKENS)  # type: ignore[arg-type]


def test_a_sub_game_line_refuses_a_number_outside_the_frozen_sequence() -> None:
    for bad in (0, 7, True):
        with pytest.raises(InvalidResultValueError):
            SubGameResult(bad, 20, 5, Outcome.CAPTURE, COMMITS, TOKENS)  # type: ignore[arg-type]


def test_the_series_outcome_is_a_validated_string_not_an_invented_enum() -> None:
    assert CumulativeResult(1, 2, "group_a_lead").series_outcome == "group_a_lead"
    with pytest.raises(InvalidResultValueError):
        CumulativeResult(1, 2, "")


@pytest.mark.parametrize("field", ["github_commit", "tokens"])
def test_a_sub_game_line_requires_exact_participant_scoped_types(field: str) -> None:
    parts = {"github_commit": COMMITS, "tokens": TOKENS}
    parts[field] = "not the right type"
    with pytest.raises(InvalidResultValueError):
        SubGameResult(1, 20, 5, Outcome.CAPTURE, parts["github_commit"], parts["tokens"])
