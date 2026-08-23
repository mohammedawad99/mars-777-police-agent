"""Turning the agreed pairing into the immutable series role assignment.

This is the **boundary**. The generic result and audit layers take a
`SeriesRoleAssignment` as an argument and never open a pairing file, so they keep
working for synthetic groups and for whatever opponent comes next. Reading what
this particular pairing agreed is a composition-layer duty, and it lives here.

**It fails closed.** A counted series that cannot say which side each group takes
has no schedule, and a schedule guessed from group-id ordering or from whichever
process is executing would be wrong in exactly half the deployments while
looking right in the other half. So a missing contract, a group the agreement
does not name, or a malformed assignment is a refusal - never an inference.

Slot ordering and role scheduling are **different concepts** and are kept apart:
`group_a`/`group_b` is a deterministic ordering of identifiers, and it says
nothing about who plays police first.
"""

from ..infra.game_contract import first_role_of
from .declaration_values import Declaration
from .kit_messages import KitRole
from .protocol_errors import LocalDefectError
from .result_core_runtime import participants_of
from .series_roles import SeriesRoleAssignment, alternating


def series_roles_for(declaration: Declaration, group_id: str) -> SeriesRoleAssignment:
    """The assignment this series runs under, or a typed refusal."""
    participants = participants_of(declaration)
    # `participants_of` already refuses a declaration naming one group twice, so
    # the two ids differ by the time we get here and no second guard is needed.
    other = participants.group_b if participants.group_a == group_id else participants.group_a
    try:
        declared = first_role_of(group_id)
    except (KeyError, OSError, ValueError) as failure:
        raise LocalDefectError(
            f"no agreed sub-game-1 role for {group_id!r}; a counted series will not"
            " infer one from process role or identifier ordering",
        ) from failure
    return alternating(group_id, KitRole(declared), other)
