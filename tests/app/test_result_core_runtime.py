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
    merged_with_distinct_role_commits,
    partial,
)

from mars777_police.app.artifact_values import GitCommitSha
from mars777_police.app.kit_messages import KitRole
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
from mars777_police.app.series_roles import alternating

ROLES = alternating(GROUP_A, KitRole.POLICE, GROUP_B)

SLOT_A = slot_of(merged(), GROUP_A)
SLOT_B = slot_of(merged(), GROUP_B)
"""Where each group actually sits, read from the declaration rather than assumed."""


def seated(scoped: object, group_id: str) -> object:
    """Read a participant-scoped value at the slot *group_id* occupies.

    These assertions are about **groups**, not about slots: which slot a group
    occupies is decided by the identifier ordering and is deliberately not a
    fixture's choice, so the test asks the declaration instead of spelling one.
    """
    return getattr(scoped, slot_of(merged(), group_id))


PAIR = (contribution(GROUP_A, COMMIT_A, 200), contribution(GROUP_B, COMMIT_B, 100))


def build(pair: object = PAIR) -> object:
    return assemble(merged(), DECLARATION_REF, LINES, pair, LINKS, CUMULATIVE, STAMP, ROLES)


def test_the_core_is_identical_whichever_side_assembles_it() -> None:
    assert build(PAIR) == build(PAIR[::-1])


def test_contributions_are_placed_by_declared_slot_not_by_argument_order() -> None:
    placed = by_slot(merged(), PAIR[::-1])
    assert placed[SLOT_A].group_id == GROUP_A
    assert placed[SLOT_B].group_id == GROUP_B


def test_total_tokens_is_derived_from_the_six_contributed_values() -> None:
    core = build()
    assert seated(core.total_tokens, GROUP_A) == sum(range(201, 207))
    assert seated(core.total_tokens, GROUP_B) == sum(range(101, 107))
    assert seated(core.total_tokens, GROUP_A) == total_tokens(PAIR[0])
    assert sum(seated(entry.tokens, GROUP_A) for entry in core.sub_games) == seated(
        core.total_tokens, GROUP_A
    )


def test_no_combined_total_exists() -> None:
    core = build()
    assert not hasattr(core.total_tokens, "combined")
    assert not hasattr(core, "tokens")


def test_each_line_carries_both_participants_commits_and_tokens() -> None:
    core = build()
    assert seated(core.sub_games[0].github_commit, GROUP_A) == COMMIT_A
    assert seated(core.sub_games[0].github_commit, GROUP_B) == COMMIT_B
    assert seated(core.sub_games[0].tokens, GROUP_A) == 201
    assert seated(core.sub_games[0].tokens, GROUP_B) == 101


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
        check_declared_commit(merged(), swapped, ROLES)
    assert failure.value.error_id == "E-REPORT-DISAGREE"


def test_one_commit_repeated_across_the_series_is_now_refused() -> None:
    """The defect the role-specific declaration exists to make impossible.

    Every row carrying the police commit was the old rule; under alternation the
    even sub-games are played from the thief repository, so a constant commit now
    misdescribes half the series and is refused at the role it claims.
    """
    declaration = merged_with_distinct_role_commits()
    with pytest.raises(ReportDisagreeError):
        check_declared_commit(declaration, contribution(GROUP_A, COMMIT_A), ROLES)


def test_two_role_commits_are_representable_and_a_third_is_not() -> None:
    """The structural bound follows the schedule, not a single-commit rule.

    A series alternates between exactly two repositories, so a participant may
    contribute two distinct commits and never more. Replacing one row is now a
    legal contribution; a third commit is still unrepresentable, which is what
    keeps `check_declared_commit` comparing against a bounded declaration.
    """
    entries = list(contribution(GROUP_A, COMMIT_A).entries)
    entries[3] = ResultContributionEntry(4, COMMIT_B, 10)
    assert ResultContribution(GROUP_A, tuple(entries)).entries[3].github_commit == COMMIT_B

    entries[5] = ResultContributionEntry(6, GitCommitSha("c" * 40), 10)
    with pytest.raises(InvalidResultValueError):
        ResultContribution(GROUP_A, tuple(entries))


def test_a_partial_declaration_cannot_produce_a_core() -> None:
    with pytest.raises(LocalDefectError):
        participants_of(partial(GROUP_A, COMMIT_A))


def test_the_participants_come_from_the_declaration_slots() -> None:
    participants = participants_of(merged())
    assert seated(participants, GROUP_A) == GROUP_A
    assert seated(participants, GROUP_B) == GROUP_B


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
            ROLES,
        )


def test_the_core_carries_the_six_lines_in_ascending_order() -> None:
    assert tuple(entry.sub_game for entry in build().sub_games) == (1, 2, 3, 4, 5, 6)


def test_no_role_ever_keys_a_participant_owned_value() -> None:
    core = build()
    for name in ("police", "thief", "cop"):
        assert not hasattr(core.total_tokens, name)
        assert not hasattr(core.sub_games[0].github_commit, name)
