"""Where a six-row schedule comes from, and the operator flag it outranks.

Sub-game 1 decides all six rows, so whatever decides sub-game 1 decides the
series. It used to be a command-line flag defaulting to `police` - which meant a
forgotten argument inverted the whole series while every process still reported
itself healthy, and three processes each holding their own copy could disagree
about which backend owned the next message.
"""

import pytest

from mars777_police.app.kit_messages import KitRole
from mars777_police.app.kit_schedule import schedule_for
from mars777_police.app.protocol_errors import LocalDefectError
from mars777_police.app.series_first_role import first_role_for
from mars777_police.first_role_source import agreed_first_role, series_first_role

OURS = "MaRs-777"
PEER = "s82kma9e"
UNNAMED = "GROUP-XY"


def test_the_contract_decides_when_it_names_the_group() -> None:
    assert series_first_role(OURS, None) is KitRole.POLICE
    assert agreed_first_role(OURS) == "police"
    assert agreed_first_role(PEER) == "thief"


def test_an_operator_who_agrees_changes_nothing() -> None:
    assert series_first_role(OURS, "police") is KitRole.POLICE


def test_an_operator_who_contradicts_the_agreement_is_refused() -> None:
    """The defect this exists to close: a flag must not invert an agreed series."""
    with pytest.raises(LocalDefectError, match="not an operator preference"):
        series_first_role(OURS, "thief")


def test_a_pairing_the_contract_does_not_name_needs_someone_to_say() -> None:
    assert agreed_first_role(UNNAMED) is None
    assert series_first_role(UNNAMED, "thief") is KitRole.THIEF
    with pytest.raises(LocalDefectError, match="none was stated"):
        series_first_role(UNNAMED, None)


def test_the_rule_is_testable_without_a_contract_on_disk() -> None:
    """The generic half takes both answers as arguments and reads no file."""
    assert first_role_for(OURS, None, "thief") is KitRole.THIEF
    assert first_role_for(OURS, "thief", None) is KitRole.THIEF
    with pytest.raises(LocalDefectError):
        first_role_for(OURS, "police", "thief")
    with pytest.raises(LocalDefectError):
        first_role_for(OURS, None, None)


def test_our_agreed_schedule_is_the_alternating_six() -> None:
    ours = schedule_for(series_first_role(OURS, None))
    assert [role.value for role in ours] == [
        "police",
        "thief",
        "police",
        "thief",
        "police",
        "thief",
    ]


def test_the_two_sides_alternate_against_each_other_in_every_row() -> None:
    """One agreement, two complementary schedules - never two independent flags."""
    ours = schedule_for(series_first_role(OURS, None))
    theirs = schedule_for(KitRole(agreed_first_role(PEER) or ""))
    assert all(a is not b for a, b in zip(ours, theirs, strict=True))


def test_both_of_our_processes_resolve_the_same_first_role() -> None:
    """The gateway and each backend read one agreement, not three flags.

    Whichever repository is executing, and whichever backend asks, the answer is
    the group's agreed first role - never the role of the process asking.
    """
    assert series_first_role(OURS, None) is series_first_role(OURS, None)
    assert series_first_role(OURS, None) is KitRole.POLICE
