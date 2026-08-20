"""One short, human word for a physical action, for anything that shows one.

A window, a command line and a replay all need to say what somebody did, and
they must say it the same way: two spellings of the same move in two views of
one match is a defect a reader would have to reconcile themselves.

**A label, never an authority.** Nothing decides anything from this string - it
is produced from an action that some owner already chose, and read only by eyes.
"""

from ..domain.actions import BarrierAction, MoveAction, PhysicalAction

UNKNOWN = "UNKNOWN"
"""What an action this build cannot name is called. It is still never guessed."""


def action_label(action: PhysicalAction) -> str:
    """A short readable name for *action*, for display and for nothing else."""
    if isinstance(action, MoveAction):
        return f"MOVE {action.move.value}"
    if isinstance(action, BarrierAction):
        return f"BARRIER {action.target.row},{action.target.col}"
    return UNKNOWN
