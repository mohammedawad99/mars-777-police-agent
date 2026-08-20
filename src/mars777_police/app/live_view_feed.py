"""The one place a running game speaks to a window, and never listens back.

The driver already holds the lawful `Observation` it is about to decide from.
This turns that value into a published snapshot and drops it in the sink -
one call, no return value, no question asked of the viewer.

**Nothing here can change a turn.** The feed has no reference to the strategy,
the turn service or the protocol runtime; it reads a value that was already
computed and hands a copy onward. Every publication goes through `GuardedSink`,
so a viewer that raises is counted rather than propagated (`PRD07-FR-008`).
"""

from dataclasses import dataclass, field

from ..domain.actions import PhysicalAction
from ..domain.observation import Observation
from .action_words import action_label
from .live_view_sink import NO_VIEWER, GuardedSink, LiveViewSink
from .live_view_values import snapshot_of
from .turn_cursor import TurnCursor

TURN = "TURN"
"""The phase word a live window shows while a round is being played."""


@dataclass(slots=True)
class LiveViewFeed:
    """A role's live projection, addressed to whoever is watching - or nobody."""

    sink: LiveViewSink = field(default=NO_VIEWER)
    role: str = field(default="agent")
    game_id: str = field(default="")
    guard: GuardedSink = field(init=False)

    def __post_init__(self) -> None:
        self.guard = GuardedSink(self.sink)

    def show(
        self,
        observation: Observation,
        cursor: TurnCursor,
        action: PhysicalAction,
        hint: str | None = None,
    ) -> None:
        """Publish this round's lawful local view. Returns nothing, raises nothing."""
        self.guard.publish(
            snapshot_of(
                observation,
                role=self.role,
                game_id=self.game_id,
                sub_game=cursor.sub_game,
                step=cursor.step,
                phase=TURN,
                last_action=action_label(action),
                hint=hint,
            )
        )
