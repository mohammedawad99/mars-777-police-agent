"""Which participant occupies which declaration slot, decided deterministically.

`group_a` and `group_b` are an **ordering of identifiers**, nothing more: the two
peers sort the exact group-id strings by Unicode code point and the lower one
takes `group_a`. Both sides must land on the same layout or they hash different
bytes and neither Step-0 proof can verify the other, so the order is derived and
checked rather than chosen and trusted.

**A slot is not a role.** It is not who plays police, not who moves first and not
which process is running. A group can legally occupy `group_b` and still take
police in sub-game 1 - the series role schedule is a separate authority and
`SeriesRoleAssignment` owns it.

No locale collation, no case folding, no role or repository ordering.
"""

from typing import Final

from .protocol_errors import StaleMessageError

PARTICIPANT_SLOTS: Final[tuple[str, str]] = ("group_a", "group_b")
"""The two slot names, in the order the sort fills them."""


def slots_for(first: str, second: str) -> dict[str, str]:
    """Map each slot to the group id that must occupy it."""
    if first == second:
        raise StaleMessageError("a pairing needs two distinct group identifiers")
    ordered = sorted((first, second))
    return dict(zip(PARTICIPANT_SLOTS, ordered, strict=True))


def slot_of(first: str, second: str, group_id: str) -> str:
    """The slot *group_id* occupies in the pairing, by code-point order."""
    for slot, occupant in slots_for(first, second).items():
        if occupant == group_id:
            return slot
    raise StaleMessageError(f"{group_id!r} is not a participant of this pairing")


def require_ordered(placed: dict[str, str]) -> None:
    """Refuse any layout other than the deterministic one.

    A layout that does not name both slots is refused first and separately: two
    subtrees claiming one slot collapse to a single entry, and reporting that as
    an ordering fault would name the wrong defect.
    """
    occupants = list(placed.values())
    if len(occupants) != len(PARTICIPANT_SLOTS):
        raise StaleMessageError(
            "each participant must occupy its own slot;"
            f" this layout fills {sorted(placed)} rather than {list(PARTICIPANT_SLOTS)}",
        )
    expected = slots_for(*occupants)
    if placed != expected:
        raise StaleMessageError(
            f"participant slots are not in identifier order: {placed} should be {expected}",
        )
