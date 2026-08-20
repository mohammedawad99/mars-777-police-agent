"""Watching a match this process is playing, without being able to touch it.

The series runs on its own thread and drops its newest lawful snapshot in a
one-slot box; the window wakes on a timer, takes whatever is there and draws it.
There is no call in the other direction - the window has no reference to a
strategy, a turn service or a socket - so a slow, broken or closed viewer costs
the match nothing (`PRD07-FR-008`).

**Polling rather than pushing, on purpose.** A toolkit callback invoked from the
game's thread would put drawing on the critical path; a timer keeps every
graphical cost inside the window's own loop, and a missed frame is simply an
older picture rather than a delayed turn.
"""

from ..app.live_view_sink import LatestSnapshot
from ..app.live_view_values import LiveViewSnapshot
from .geometry import window_size
from .live_layout import live_frame
from .window import GameWindow

REFRESH_MS = 200
"""How often the window looks in the box. Purely a viewer's own timing."""


def waiting(role: str, game_id: str) -> LiveViewSnapshot:
    """What to show before the first turn: an empty local view, honestly labelled."""
    return LiveViewSnapshot(
        role=role,
        game_id=game_id,
        sub_game=0,
        step=0,
        phase="WAITING",
        grid_size=1,
        own_cell=(0, 0),
        barriers=(),
    )


def open_window(box: LatestSnapshot, role: str, game_id: str) -> GameWindow:
    """A window that redraws itself from *box* every `REFRESH_MS` milliseconds."""
    opening = box.take() or waiting(role, game_id)
    width, height = window_size(max(opening.grid_size, 8))
    window = GameWindow(title=f"live {game_id}", width=width, height=height)

    def tick() -> None:
        snapshot = box.take()
        if snapshot is not None:
            window.draw(live_frame(snapshot, width, height))
        window.root.after(REFRESH_MS, tick)

    window.draw(live_frame(opening, width, height))
    window.root.after(REFRESH_MS, tick)
    return window
