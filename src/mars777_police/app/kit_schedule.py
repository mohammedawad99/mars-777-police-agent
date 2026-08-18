"""Which side we take in each of the six sub-games, decided before any of them.

**Provenance, stated plainly.** Role alternation is **not** a binding course-book
requirement - the book's body never states it. It is the reference
implementation's convention and a de-facto league practice, and the pinned
network harness mandates it: `netplay.py` computes `role_for(natural, n)` inside
its per-sub-game loop, and its `--role` flag selects only the side it takes in
**sub-game 1**.

So the whole series schedule is a pure function of two things agreed out of
band - the frozen `SeriesConvention` and who plays what in sub-game 1 - and is
never derived from a source port, a process id, an arrival time or a strategy
output. Pinning all six rows before gameplay is what lets a mismatch be caught
as a mismatch instead of being played out.
"""

from .interop_profiles import SeriesConvention
from .kit_messages import KitRole
from .protocol_errors import StaleMessageError

SUB_GAMES = 6
"""App F Table 18 #1: a series is six sub-games, and the schedule has six rows."""

CONVENTION = SeriesConvention.REFERENCE_ODD_EVEN_ALTERNATION
"""The one convention this schedule implements. No second convention exists."""


def role_for(first: KitRole, sub_game: int) -> KitRole:
    """Our side in *sub_game*: the agreed first role on odd, its other on even."""
    if not 1 <= sub_game <= SUB_GAMES:
        raise StaleMessageError(
            f"sub-game {sub_game} is outside a six-sub-game series, so it has no role",
        )
    if sub_game % 2 == 1:
        return first
    return KitRole.THIEF if first is KitRole.POLICE else KitRole.POLICE


def schedule_for(first: KitRole) -> tuple[KitRole, ...]:
    """All six rows, in order, so a mismatch is caught before it is played."""
    return tuple(role_for(first, number) for number in range(1, SUB_GAMES + 1))
