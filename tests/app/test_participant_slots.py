"""Which participant sits in which slot, and every layout that is refused.

`group_a`/`group_b` order identifiers and nothing else. Both peers must derive
the same seating or they hash different bytes and neither Step-0 proof verifies,
so the layout is computed and checked rather than chosen and trusted.

The separation these tests defend: a slot is not a role, not a first mover and
not the running process. A group can sit in `group_b` and still take police in
sub-game 1.
"""

import pytest

from mars777_police.app.kit_messages import KitRole
from mars777_police.app.participant_slots import (
    PARTICIPANT_SLOTS,
    require_ordered,
    slot_of,
    slots_for,
)
from mars777_police.app.protocol_errors import StaleMessageError
from mars777_police.app.series_roles import alternating

MARS = "MaRs-777"
PEER = "s82kma9e"
SYNTHETIC = "GROUP-XY"


def test_the_real_pairing_seats_mars_first() -> None:
    """`M` (U+004D) precedes `s` (U+0073), so MaRs takes group_a."""
    assert slots_for(MARS, PEER) == {"group_a": MARS, "group_b": PEER}
    assert slot_of(MARS, PEER, MARS) == "group_a"
    assert slot_of(MARS, PEER, PEER) == "group_b"


def test_the_synthetic_pairing_seats_mars_second() -> None:
    """`G` (U+0047) precedes `M`, so the synthetic group takes group_a."""
    assert slots_for(MARS, SYNTHETIC) == {"group_a": SYNTHETIC, "group_b": MARS}
    assert slot_of(MARS, SYNTHETIC, MARS) == "group_b"


def test_the_order_is_argument_independent() -> None:
    """Both peers derive the same seating whichever way they hold the pair."""
    assert slots_for(MARS, PEER) == slots_for(PEER, MARS)
    assert slots_for(MARS, SYNTHETIC) == slots_for(SYNTHETIC, MARS)


def test_the_ordering_is_code_point_not_case_folded() -> None:
    """No locale collation and no case folding: uppercase sorts first."""
    assert slots_for("a-group", "B-group") == {"group_a": "B-group", "group_b": "a-group"}


def test_a_pairing_needs_two_distinct_identifiers() -> None:
    with pytest.raises(StaleMessageError, match="two distinct group identifiers"):
        slots_for(MARS, MARS)


def test_a_group_outside_the_pairing_has_no_slot() -> None:
    with pytest.raises(StaleMessageError, match="not a participant"):
        slot_of(MARS, PEER, SYNTHETIC)


def test_the_correct_layout_is_accepted() -> None:
    require_ordered({"group_a": MARS, "group_b": PEER})
    require_ordered({"group_a": SYNTHETIC, "group_b": MARS})


def test_a_reversed_layout_is_refused() -> None:
    with pytest.raises(StaleMessageError, match="not in identifier order"):
        require_ordered({"group_a": PEER, "group_b": MARS})
    with pytest.raises(StaleMessageError, match="not in identifier order"):
        require_ordered({"group_a": MARS, "group_b": SYNTHETIC})


def test_a_layout_naming_one_group_twice_is_refused() -> None:
    with pytest.raises(StaleMessageError):
        require_ordered({"group_a": MARS, "group_b": MARS})


def test_a_layout_that_leaves_a_slot_empty_names_that_fault() -> None:
    """Two subtrees claiming one slot collapse to one entry, not to a bad order.

    The refusal has to say which defect it found, because "not in identifier
    order" would send whoever reads it looking for the wrong thing.
    """
    with pytest.raises(StaleMessageError, match="must occupy its own slot"):
        require_ordered({"group_b": PEER})
    with pytest.raises(StaleMessageError, match="must occupy its own slot"):
        require_ordered({})


def test_slot_order_and_role_schedule_are_independent() -> None:
    """The separation, stated as an executable fact.

    In the synthetic pairing MaRs sits in `group_b` and still plays police in
    sub-game 1. Anything deriving a role from a slot would invert this.
    """
    seating = slots_for(MARS, SYNTHETIC)
    roles = alternating(MARS, KitRole.POLICE, SYNTHETIC)
    assert seating["group_b"] == MARS
    assert roles.role_of(MARS, 1) is KitRole.POLICE
    assert roles.role_of(SYNTHETIC, 1) is KitRole.THIEF
    assert [roles.role_of(MARS, n).value for n in range(1, 7)] == [
        "police",
        "thief",
        "police",
        "thief",
        "police",
        "thief",
    ]


def test_the_slot_names_are_the_two_frozen_ones() -> None:
    assert PARTICIPANT_SLOTS == ("group_a", "group_b")
