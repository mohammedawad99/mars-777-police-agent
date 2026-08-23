"""Which of a group's two processes sends its one report, and why not both.

Rule 35 credits a group for its own report and scores a *contradictory* one 0 for
both groups. Under `FIXED_ROLE` exactly one MaRs-777 process existed, so nothing
had to decide; under the agreed alternating convention both role backends run,
both play three sub-games and both reach the dispatch point.
"""

from mars777_police.app.kit_messages import KitRole
from mars777_police.app.kit_schedule import SUB_GAMES, schedule_for
from mars777_police.app.report_owner import reporting_role, reports_for_group
from mars777_police.first_role_source import series_first_role


def test_exactly_one_of_the_two_roles_reports() -> None:
    for first in (KitRole.POLICE, KitRole.THIEF):
        owners = [role for role in KitRole if reports_for_group(first, role)]
        assert owners == [reporting_role(first)]
        assert len(owners) == 1


def test_the_owner_is_whoever_plays_the_final_sub_game() -> None:
    """Not a named repository: the side holding the settled result at the end."""
    for first in (KitRole.POLICE, KitRole.THIEF):
        assert reporting_role(first) is schedule_for(first)[SUB_GAMES - 1]


def test_under_our_agreement_the_thief_repository_reports() -> None:
    """MaRs-777 is police first, so sub-game 6 is ours as thief."""
    agreed = series_first_role("MaRs-777", None)
    assert agreed is KitRole.POLICE
    assert reporting_role(agreed) is KitRole.THIEF
    assert reports_for_group(agreed, KitRole.THIEF)
    assert not reports_for_group(agreed, KitRole.POLICE)


def test_the_owner_follows_a_flipped_agreement_rather_than_going_stale() -> None:
    """Hard-coding "thief" would silently misreport if the agreement ever changed."""
    assert reporting_role(KitRole.THIEF) is KitRole.POLICE
    assert reports_for_group(KitRole.THIEF, KitRole.POLICE)
    assert not reports_for_group(KitRole.THIEF, KitRole.THIEF)


def test_the_reporter_and_the_settlement_waiter_are_the_same_side() -> None:
    """The process holding the settled result is the one that reports it."""
    from mars777_police.app.kit_settlement import plays_final_sub_game

    for first in (KitRole.POLICE, KitRole.THIEF):
        owner = reporting_role(first)
        rows = schedule_for(first)
        owned = tuple(n for n, role in enumerate(rows, start=1) if role is owner)
        assert plays_final_sub_game(owned)
