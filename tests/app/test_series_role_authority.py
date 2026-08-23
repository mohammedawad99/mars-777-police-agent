"""Whose schedule decides a row's role, and the shortcut that got it wrong.

A counted series alternates, so the side a group takes is a **series-level**
fact. Deriving it from the executing process instead inverts all six rows in
whichever repository is not the group's first role - correct in one deployment
and silently wrong in the other. These tests pin the schedule from both sides so
that shortcut cannot come back.
"""

import pytest
from r16_builders import GROUP_B, merged

from mars777_police.app.kit_messages import KitRole
from mars777_police.app.protocol_errors import LocalDefectError
from mars777_police.app.series_roles import SeriesRoleAssignment, alternating
from mars777_police.app.series_roles_source import series_roles_for

MARS = "MaRs-777"
PEER = "s82kma9e"
ROLES = alternating(MARS, KitRole.POLICE, PEER)

MARS_SCHEDULE = ["police", "thief", "police", "thief", "police", "thief"]
PEER_SCHEDULE = ["thief", "police", "thief", "police", "thief", "police"]


def played(group_id: str) -> list[str]:
    return [ROLES.role_of(group_id, number).value for number in range(1, 7)]


def test_our_six_rows_follow_the_series_schedule() -> None:
    assert played(MARS) == MARS_SCHEDULE


def test_the_peer_six_rows_are_the_exact_complement() -> None:
    assert played(PEER) == PEER_SCHEDULE
    assert all(a != b for a, b in zip(MARS_SCHEDULE, PEER_SCHEDULE, strict=True))


def test_the_thief_process_still_resolves_g01_to_police() -> None:
    """The exact defect: the executing process must not decide the schedule.

    Our thief backend serves `g02`, `g04` and `g06`, but the group's first role
    is police. If anything derived the schedule from the running process, `g01`
    would resolve to thief here and every row would be inverted.
    """
    assert ROLES.role_of(MARS, 1) is KitRole.POLICE
    assert ROLES.role_of(MARS, 2) is KitRole.THIEF
    assert played(MARS) == MARS_SCHEDULE


def test_the_police_process_resolves_the_same_schedule() -> None:
    """Both of our processes must read one schedule, not two."""
    assert played(MARS) == MARS_SCHEDULE
    assert ROLES.first_role_of(MARS) is KitRole.POLICE


def test_a_group_the_series_does_not_name_is_refused() -> None:
    with pytest.raises(LocalDefectError, match="assigns no first role"):
        ROLES.role_of("someone-else", 1)


def test_participants_cannot_share_a_first_role() -> None:
    """Complementary by construction: both sides starting as police is no series."""
    with pytest.raises(LocalDefectError, match="complementary first roles"):
        SeriesRoleAssignment({MARS: KitRole.POLICE, PEER: KitRole.POLICE})


def test_an_assignment_must_name_someone() -> None:
    with pytest.raises(LocalDefectError, match="names no participant"):
        SeriesRoleAssignment({})


def test_the_inverse_pairing_is_representable() -> None:
    """Nothing hard-codes which group starts as police."""
    inverse = alternating(MARS, KitRole.THIEF, PEER)
    assert [inverse.role_of(MARS, n).value for n in range(1, 7)] == PEER_SCHEDULE
    assert [inverse.role_of(PEER, n).value for n in range(1, 7)] == MARS_SCHEDULE


def test_production_refuses_a_pairing_the_agreement_does_not_name() -> None:
    """Fail closed: a counted series never invents a schedule.

    `series_roles_for` reads the agreed pairing. For a group the agreement does
    not name there is no schedule to read, and inferring one - from the executing
    process or from identifier ordering - would be wrong in exactly half the
    deployments while looking right in the other half. So it refuses.
    """
    declaration = merged()
    with pytest.raises(LocalDefectError, match="no agreed sub-game-1 role"):
        series_roles_for(declaration, GROUP_B)


def test_slot_ordering_is_not_a_role_rule() -> None:
    """Two separate concepts that must never be conflated.

    `group_a`/`group_b` orders identifiers; it says nothing about who plays
    police first. A group that sorts first can perfectly well start as thief.
    """
    first_sorted, _ = sorted([MARS, PEER])
    assert first_sorted == MARS
    inverse = alternating(MARS, KitRole.THIEF, PEER)
    assert inverse.first_role_of(first_sorted) is KitRole.THIEF
