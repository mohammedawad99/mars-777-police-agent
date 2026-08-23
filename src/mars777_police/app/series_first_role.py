"""Where a series' first role comes from, and the operator input it outranks.

The whole six-row schedule is a pure function of the frozen convention and who
plays what in sub-game 1, so sub-game 1 is the single value that decides every
row. Reading it from a command-line flag - which is what this replaces - made an
operator's typo, or a forgotten argument, silently invert the entire series
while every process still reported itself healthy. Worse, three processes each
took their own copy of it: a gateway and two backends that disagreed would route
each message to the backend playing the other side.

So when the frozen shared contract names our group, **the contract decides** and
an operator value that contradicts it is refused rather than obeyed. The flag
survives only for pairings the contract does not name - a synthetic opponent, a
local rehearsal - where there is no agreement to read and someone has to say.

Deliberately not a fallback: a contract that names the group and a flag that
disagrees is not a preference to reconcile, it is two statements about one
agreement of which exactly one can be true.
"""

from .kit_messages import KitRole
from .protocol_errors import LocalDefectError


def first_role_for(group_id: str, declared: str | None, agreed: str | None) -> KitRole:
    """The side *group_id* takes in sub-game 1, from the agreement where there is one.

    *agreed* is the frozen contract's answer, or `None` when it names no role for
    this group; *declared* is what the operator typed, or `None` when they typed
    nothing. One of the two must exist, because a series with no first role has
    no schedule and must not be played on a guess.
    """
    if agreed is not None:
        if declared is not None and declared != agreed:
            raise LocalDefectError(
                f"the shared contract gives {group_id!r} {agreed!r} in sub-game 1 and this"
                f" process was told {declared!r}; the agreement is not an operator preference",
            )
        return KitRole(agreed)
    if declared is None:
        raise LocalDefectError(
            f"no agreed first role for {group_id!r} and none was stated; a series schedule"
            " is not inferred from the running process or from a default",
        )
    return KitRole(declared)
