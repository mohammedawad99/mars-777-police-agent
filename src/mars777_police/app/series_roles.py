"""Which side each participant takes, for every sub-game of one series.

A **series-level** fact, and deliberately not a process-level one. Two mistakes
this value exists to make unrepresentable:

*A process's own role is not its group's first role.* Under
`REFERENCE_ODD_EVEN_ALTERNATION` a group plays its first role in the odd
sub-games and the other in the even ones, so the group that starts as police
runs its thief backend for `g02`, `g04` and `g06`. Reading the schedule from
whichever process happens to be executing inverts all six rows in exactly half
the deployments - correct in one repository, silently wrong in the other.

*One first role cannot describe both participants.* The two sides are
complementary: if we start as police they start as thief. A single scalar
therefore mis-describes whichever participant it was not taken from, which
matters because the result core validates **both** contributions.

The assignment is passed **in** rather than read from a pairing file: this layer
is generic and must work for synthetic groups and for any future opponent, so
the composition root builds the value from whatever the pairing agreed and hands
it over. Nothing here knows a group id in advance.
"""

from collections.abc import Mapping
from dataclasses import dataclass

from .kit_messages import KitRole
from .kit_schedule import role_for
from .protocol_errors import LocalDefectError


@dataclass(frozen=True, slots=True)
class SeriesRoleAssignment:
    """Each participant's sub-game-1 side, frozen before the series starts."""

    first_roles: Mapping[str, KitRole]

    def __post_init__(self) -> None:
        if not self.first_roles:
            raise LocalDefectError("a series role assignment names no participant")
        roles = set(self.first_roles.values())
        if len(self.first_roles) > 1 and len(roles) != len(self.first_roles):
            raise LocalDefectError(
                "participants must take complementary first roles;"
                f" {sorted(self.first_roles)} all start as {roles.pop().value}",
            )

    def first_role_of(self, group_id: str) -> KitRole:
        """The side *group_id* takes in sub-game 1, or a typed local refusal."""
        role = self.first_roles.get(group_id)
        if role is None:
            raise LocalDefectError(f"this series assigns no first role to {group_id!r}")
        return role

    def role_of(self, group_id: str, sub_game: int) -> KitRole:
        """The side *group_id* actually plays in *sub_game*, from the schedule."""
        return role_for(self.first_role_of(group_id), sub_game)


def alternating(first: str, first_role: KitRole, second: str) -> SeriesRoleAssignment:
    """The two-participant assignment the reference convention implies."""
    other = KitRole.THIEF if first_role is KitRole.POLICE else KitRole.POLICE
    return SeriesRoleAssignment({first: first_role, second: other})
