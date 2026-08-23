"""The result approval core: exact membership, explicit vocabulary, one digest.

Both peers must produce identical bytes from the same semantic inputs, so the
projection is checked member by member and the digest is checked to be
insensitive to construction order but sensitive to every value.
"""

import pytest
from r16_builders import (
    COMMIT_A,
    COMMIT_B,
    CUMULATIVE,
    DECLARATION_REF,
    GROUP_A,
    GROUP_B,
    LINES,
    LINKS,
    STAMP,
    contribution,
    merged,
)

from mars777_police.app.kit_messages import KitRole
from mars777_police.app.protocol_errors import LocalDefectError
from mars777_police.app.result_core_runtime import assemble
from mars777_police.app.result_values import ParticipantTokenUsage
from mars777_police.app.series_roles import alternating
from mars777_police.domain.terminal import Outcome
from mars777_police.protocol.canonical import canonical_json_bytes
from mars777_police.protocol.result_core import (
    OUTCOME_TOKENS,
    ResultDigester,
    outcome_token,
    result_core,
)

ROLES = alternating(GROUP_A, KitRole.POLICE, GROUP_B)

PAIR = (contribution(GROUP_A, COMMIT_A, 200), contribution(GROUP_B, COMMIT_B, 100))


def core() -> object:
    return assemble(merged(), DECLARATION_REF, LINES, PAIR, LINKS, CUMULATIVE, STAMP, ROLES)


def test_the_core_carries_exactly_the_frozen_top_level_members() -> None:
    projected = result_core(core())  # type: ignore[arg-type]
    assert set(projected) == {
        "game_id",
        "game_uid",
        "declaration_ref",
        "teams",
        "github_links",
        "sub_games",
        "cumulative",
        "total_tokens",
        "timestamp",
    }


def test_the_excluded_members_are_absent_from_the_hashed_bytes() -> None:
    raw = canonical_json_bytes(result_core(core()))  # type: ignore[arg-type]
    for forbidden in (b"result_sha256", b"mutual_agreement", b"reported_by", b"accepted"):
        assert forbidden not in raw


def test_each_sub_game_line_carries_its_six_members() -> None:
    projected = result_core(core())  # type: ignore[arg-type]
    lines = projected["sub_games"]
    assert isinstance(lines, list)
    assert len(lines) == 6
    assert set(lines[0]) == {
        "sub_game",
        "cop_score",
        "thief_score",
        "outcome",
        "github_commit",
        "tokens",
    }


def test_the_participant_scoped_members_carry_both_groups() -> None:
    projected = result_core(core())  # type: ignore[arg-type]
    lines = projected["sub_games"]
    assert isinstance(lines, list)
    assert lines[0]["github_commit"] == {"group_a": COMMIT_B.value, "group_b": COMMIT_A.value}
    assert lines[0]["tokens"] == {"group_a": 101, "group_b": 201}
    assert projected["total_tokens"] == {"group_a": 621, "group_b": 1221}


def test_the_outcome_vocabulary_is_an_explicit_table_not_a_case_transform() -> None:
    assert OUTCOME_TOKENS == {
        Outcome.CAPTURE: "capture",
        Outcome.SURVIVAL: "survival",
        Outcome.TECHNICAL_LOSS: "technical_loss",
    }
    for member in Outcome:
        assert outcome_token(member) == member.value.lower()
        assert outcome_token(member) != member.value


def test_no_tie_outcome_is_invented_for_a_sub_game() -> None:
    """Ch 3 Table 2 has no tie end event, so no sub-game can carry one."""
    assert "tie" not in OUTCOME_TOKENS.values()
    assert not hasattr(Outcome, "TIE")


def test_an_unmapped_outcome_raises_rather_than_being_transformed() -> None:
    with pytest.raises(LocalDefectError):
        outcome_token("capture")  # type: ignore[arg-type]


def test_the_teams_member_carries_the_two_group_ids_by_slot() -> None:
    projected = result_core(core())  # type: ignore[arg-type]
    assert projected["teams"] == {
        "group_a": {"group_id": GROUP_B},
        "group_b": {"group_id": GROUP_A},
    }


def test_the_four_links_are_a_fixed_four_key_object() -> None:
    projected = result_core(core())  # type: ignore[arg-type]
    links = projected["github_links"]
    assert isinstance(links, dict)
    assert set(links) == {"group_a_police", "group_a_thief", "group_b_police", "group_b_thief"}


def test_the_digest_is_deterministic_and_order_independent() -> None:
    digester = ResultDigester()
    first = digester.digest(core())  # type: ignore[arg-type]
    reversed_pair = assemble(
        merged(), DECLARATION_REF, LINES, PAIR[::-1], LINKS, CUMULATIVE, STAMP, ROLES
    )
    assert digester.digest(reversed_pair) == first
    assert len(first.value) == 64


def test_changing_one_token_count_changes_the_digest() -> None:
    digester = ResultDigester()
    moved = assemble(
        merged(),
        DECLARATION_REF,
        LINES,
        (contribution(GROUP_A, COMMIT_A, 201), PAIR[1]),
        LINKS,
        CUMULATIVE,
        STAMP,
        ROLES,
    )
    assert digester.digest(moved) != digester.digest(core())  # type: ignore[arg-type]
    assert moved.total_tokens != ParticipantTokenUsage(1221, 621)
