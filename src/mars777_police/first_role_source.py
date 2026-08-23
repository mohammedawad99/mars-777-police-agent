"""The composition boundary that asks the frozen contract for our first role.

Separated from `series_first_role` for the same reason `series_roles_source` is
separated from `series_roles`: the rule is generic and testable without a file
on disk, and only this layer knows that the agreement lives in a shipped JSON
document. A contract that cannot be read, or that names no role for us, is
reported as *absent* rather than as an error - `first_role_for` then decides
whether an operator value may stand in, and it is the only place that decides.
"""

from .app.kit_messages import KitRole
from .app.series_first_role import first_role_for
from .infra.game_contract import first_role_of


def agreed_first_role(group_id: str) -> str | None:
    """What the shipped contract says, or `None` when it says nothing about us."""
    try:
        return first_role_of(group_id)
    except (KeyError, OSError, ValueError):
        return None


def series_first_role(group_id: str, declared: str | None) -> KitRole:
    """Resolve this series' first role from the agreement and the operator input."""
    return first_role_for(group_id, declared, agreed_first_role(group_id))
