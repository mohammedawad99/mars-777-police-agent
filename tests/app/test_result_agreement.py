"""ResultAgreement: the frozen event-14 request value."""

import dataclasses

import pytest
from result_builders import DECLARATION_REF, GAME_ID, STAMP, agreement, contribution

from mars777_police.app.artifact_values import UtcTimestamp
from mars777_police.app.peer_final_messages import ResultAgreement
from mars777_police.app.result_values import InvalidResultValueError


def test_valid_agreement() -> None:
    value = agreement()
    assert value.game_id == GAME_ID
    assert value.declaration_ref == DECLARATION_REF
    assert value.timestamp == UtcTimestamp(STAMP)


def test_agreement_field_order() -> None:
    assert [f.name for f in dataclasses.fields(ResultAgreement)] == [
        "game_id",
        "game_uid",
        "declaration_ref",
        "timestamp",
        "contribution",
    ]


def test_agreement_carries_no_digest_flag_or_cursor() -> None:
    names = {f.name for f in dataclasses.fields(ResultAgreement)}
    assert not names & {
        "result_sha256",
        "accepted",
        "ok",
        "mutual_agreement",
        "reported_by",
        "scores",
        "cumulative",
        "total_tokens",
        "github_links",
        "cursor",
        "step",
        "phase",
        "sub_game",
        "verdict",
        "auth",
    }


@pytest.mark.parametrize("field", ["game_id", "game_uid", "declaration_ref"])
@pytest.mark.parametrize("bad", [None, 1, True])
def test_identity_members_must_be_str(field: str, bad: object) -> None:
    with pytest.raises(InvalidResultValueError, match=f"{field} must be a str"):
        agreement(**{field: bad})


@pytest.mark.parametrize("field", ["game_id", "game_uid", "declaration_ref"])
def test_identity_members_must_be_non_empty(field: str) -> None:
    with pytest.raises(InvalidResultValueError, match=f"{field} must be non-empty"):
        agreement(**{field: ""})


@pytest.mark.parametrize(
    "bad",
    [
        "declaration_other-game.json",
        f"declaration_{GAME_ID}.JSON",
        f"declaration_{GAME_ID}",
        f"artifacts/declaration_{GAME_ID}.json",
        f"./declaration_{GAME_ID}.json",
        f" declaration_{GAME_ID}.json",
    ],
)
def test_declaration_ref_must_match_the_game_id_exactly(bad: str) -> None:
    with pytest.raises(InvalidResultValueError, match="declaration_ref must be"):
        agreement(declaration_ref=bad)


def test_a_different_game_id_needs_a_different_declaration_ref() -> None:
    with pytest.raises(InvalidResultValueError, match="declaration_ref must be"):
        agreement(game_id="other-game")
    assert (
        agreement(game_id="other-game", declaration_ref="declaration_other-game.json").game_id
        == "other-game"
    )


@pytest.mark.parametrize("bad", [STAMP, None, 1])
def test_timestamp_must_be_the_shared_value_type(bad: object) -> None:
    with pytest.raises(InvalidResultValueError, match="timestamp must be a UtcTimestamp"):
        agreement(timestamp=bad)


@pytest.mark.parametrize("bad", [{"group_id": "MaRs-777"}, None, "MaRs-777"])
def test_contribution_must_be_the_real_value(bad: object) -> None:
    with pytest.raises(InvalidResultValueError, match="contribution must be a ResultContribution"):
        agreement(contribution=bad)


def test_agreement_reuses_the_contribution_by_identity() -> None:
    value = contribution()
    assert agreement(contribution=value).contribution is value


def test_agreement_is_immutable() -> None:
    with pytest.raises(dataclasses.FrozenInstanceError):
        agreement().game_uid = "other"  # type: ignore[misc]
