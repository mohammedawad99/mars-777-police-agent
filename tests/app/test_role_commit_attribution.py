"""Attribution: which of a participant's two commits belongs to which row.

Split from the core-runtime tests because it answers a different question. Those
prove the core is assembled identically by either peer; this proves that a
contribution using only legal commits can still be wrong, and that the semantic
check is what notices.
"""

import pytest
from r16_builders import GROUP_A, merged_with_distinct_role_commits

from mars777_police.app.kit_messages import KitRole
from mars777_police.app.protocol_errors import ReportDisagreeError
from mars777_police.app.result_core_runtime import check_declared_commit
from mars777_police.app.result_values import ResultContribution, ResultContributionEntry
from mars777_police.app.series_record import own_team
from mars777_police.app.series_roles import alternating

ROLES = alternating(GROUP_A, KitRole.POLICE, "GROUP-XY")


def test_an_inverted_sequence_of_the_two_legal_commits_is_rejected() -> None:
    """The exact case the structural `<= 2 distinct` bound cannot detect.

    Every row here carries one of the two commits the participant really
    declared, and there are only two distinct values - so `ResultContribution`
    accepts it without complaint. It is still wrong: the odd sub-games are played
    as police and carry the thief commit, and the even ones the reverse. Only the
    semantic check, against the role each sub-game was actually played in, sees
    it.
    """
    declaration = merged_with_distinct_role_commits()
    commits = own_team(declaration, GROUP_A).github_commits
    inverted = tuple(
        ResultContributionEntry(
            number,
            commits.thief if number % 2 else commits.police,
            10 * number,
        )
        for number in range(1, 7)
    )
    swapped = ResultContribution(GROUP_A, inverted)
    assert len({entry.github_commit for entry in swapped.entries}) == 2

    with pytest.raises(ReportDisagreeError, match="did not declare for the police role"):
        check_declared_commit(declaration, swapped, ROLES)
