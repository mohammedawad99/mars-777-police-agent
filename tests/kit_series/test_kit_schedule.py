"""The six-row role schedule, and the handoff that walks it.

Role alternation is **reference/de-facto interoperability, not book law**: the
course book's body never states it. It appears in the reference implementation
and in the sample artifacts' own schema text, and the pinned network harness
mandates it - `netplay.py` calls `role_for(natural, n)` inside its per-sub-game
loop, and `--role` picks only the side it takes in **sub-game 1**.

So the schedule is derived from one agreed starting assignment plus the frozen
convention, and never from a source port, a process id, an arrival time or a
strategy output.
"""

import pytest

from mars777_police.app.interop_profiles import SeriesConvention
from mars777_police.app.kit_messages import KitRole
from mars777_police.app.kit_schedule import SUB_GAMES, role_for, schedule_for
from mars777_police.app.protocol_errors import StaleMessageError


def test_the_schedule_alternates_from_the_agreed_first_role() -> None:
    assert schedule_for(KitRole.POLICE) == (
        KitRole.POLICE,
        KitRole.THIEF,
        KitRole.POLICE,
        KitRole.THIEF,
        KitRole.POLICE,
        KitRole.THIEF,
    )


def test_starting_as_thief_produces_the_complementary_schedule() -> None:
    police = schedule_for(KitRole.POLICE)
    thief = schedule_for(KitRole.THIEF)

    assert all(a is not b for a, b in zip(police, thief, strict=True))


def test_it_is_exactly_six_rows() -> None:
    assert len(schedule_for(KitRole.POLICE)) == SUB_GAMES == 6


@pytest.mark.parametrize("number", [1, 2, 3, 4, 5, 6])
def test_each_row_is_the_odd_even_rule_the_reference_defines(number: int) -> None:
    expected = KitRole.POLICE if number % 2 == 1 else KitRole.THIEF

    assert role_for(KitRole.POLICE, number) is expected


def test_a_sub_game_outside_the_series_has_no_row() -> None:
    for number in (0, 7, -1):
        with pytest.raises(StaleMessageError):
            role_for(KitRole.POLICE, number)


def test_the_convention_is_the_project_enum_and_not_a_new_one() -> None:
    """`REFERENCE_ODD_EVEN_ALTERNATION` already existed; nothing was invented."""
    assert SeriesConvention.REFERENCE_ODD_EVEN_ALTERNATION.value == (
        "REFERENCE_ODD_EVEN_ALTERNATION"
    )
