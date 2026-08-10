"""Assembling the shared core: the same inputs, the same bytes, either side.

The assembly must not depend on who performs it. Every test here builds the core
twice - once with the contributions in each order - and requires the two results
to be equal, which is exactly the property that was missing before the
participant-scoped members existed.
"""

from dataclasses import replace

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
    partial,
)

from mars777_police.app.protocol_errors import LocalDefectError, ReportDisagreeError
from mars777_police.app.result_core_runtime import (
    assemble,
    by_slot,
    check_declared_commit,
    participants_of,
    slot_of,
    total_tokens,
)
from mars777_police.app.result_values import (
    InvalidResultValueError,
    ResultContribution,
    ResultContributionEntry,
)

PAIR = (contribution(GROUP_A, COMMIT_A, 200), contribution(GROUP_B, COMMIT_B, 100))


def build(pair: object = PAIR) -> object:
    return assemble(merged(), DECLARATION_REF, LINES, pair, LINKS, CUMULATIVE, STAMP)


def test_the_core_is_identical_whichever_side_assembles_it() -> None:
    assert build(PAIR) == build(PAIR[::-1])


def test_contributions_are_placed_by_declared_slot_not_by_argument_order() -> None:
    placed = by_slot(merged(), PAIR[::-1])
    assert placed["group_a"].group_id == GROUP_A
    assert placed["group_b"].group_id == GROUP_B


def test_total_tokens_is_derived_from_the_six_contributed_values() -> None:
    core = build()
    assert core.total_tokens.group_a == sum(range(201, 207))
    assert core.total_tokens.group_b == sum(range(101, 107))
    assert core.total_tokens.group_a == total_tokens(PAIR[0])
    assert sum(entry.tokens.group_a for entry in core.sub_games) == core.total_tokens.group_a


def test_no_combined_total_exists() -> None:
    core = build()
    assert not hasattr(core.total_tokens, "combined")
    assert not hasattr(core, "tokens")


def test_each_line_carries_both_participants_commits_and_tokens() -> None:
    core = build()
    assert core.sub_games[0].github_commit.group_a == COMMIT_A
    assert core.sub_games[0].github_commit.group_b == COMMIT_B
    assert core.sub_games[0].tokens.group_a == 201
    assert core.sub_games[0].tokens.group_b == 101


def test_a_contribution_from_an_undeclared_participant_is_refused() -> None:
    stranger = contribution("GROUP-ZZ", COMMIT_A)
    with pytest.raises(ReportDisagreeError):
        by_slot(merged(), (stranger, PAIR[1]))
    with pytest.raises(ReportDisagreeError):
        slot_of(merged(), "GROUP-ZZ")


def test_two_contributions_claiming_one_slot_are_refused() -> None:
    with pytest.raises(ReportDisagreeError):
        by_slot(merged(), (PAIR[0], contribution(GROUP_A, COMMIT_A)))


def test_a_commit_the_participant_did_not_declare_is_refused() -> None:
    swapped = contribution(GROUP_A, COMMIT_B)
    with pytest.raises(ReportDisagreeError) as failure:
        check_declared_commit(merged(), swapped)
    assert failure.value.error_id == "E-REPORT-DISAGREE"


def test_a_mixed_commit_contribution_never_reaches_this_layer() -> None:
    """The R15 structural invariant already makes it unrepresentable.

    That is why `check_declared_commit` compares against the declaration and
    nothing else - it can rely on all six contributed commits being equal.
    """
    entries = list(contribution(GROUP_A, COMMIT_A).entries)
    entries[3] = ResultContributionEntry(4, COMMIT_B, 10)
    with pytest.raises(InvalidResultValueError):
        ResultContribution(GROUP_A, tuple(entries))


def test_a_partial_declaration_cannot_produce_a_core() -> None:
    with pytest.raises(LocalDefectError):
        participants_of(partial(GROUP_A, COMMIT_A, "group_a"))


def test_the_participants_come_from_the_declaration_slots() -> None:
    participants = participants_of(merged())
    assert participants.group_a == GROUP_A
    assert participants.group_b == GROUP_B


def test_a_line_misaligned_with_the_contributed_sub_game_is_refused() -> None:
    shifted = replace(LINES[0], sub_game=2)
    with pytest.raises(ReportDisagreeError):
        assemble(
            merged(),
            DECLARATION_REF,
            (shifted, *LINES[1:]),
            PAIR,
            LINKS,
            CUMULATIVE,
            STAMP,
        )


def test_the_core_carries_the_six_lines_in_ascending_order() -> None:
    assert tuple(entry.sub_game for entry in build().sub_games) == (1, 2, 3, 4, 5, 6)


def test_no_role_ever_keys_a_participant_owned_value() -> None:
    core = build()
    for name in ("police", "thief", "cop"):
        assert not hasattr(core.total_tokens, name)
        assert not hasattr(core.sub_games[0].github_commit, name)
