"""Stepping through a finished sub-game in a window, forwards and backwards.

Navigation only. Every value on screen - the verification word, the semantic
verdict, whether the audit is complete - was decided by `ReplaySession` and
`audit_complete` before this module existed, and no key here can change one.

The cursor keys and `Home`/`End` are bound to the session's own movements, so
the window has exactly the freedom the replay authority already offered a
command-line reader.
"""

from ..app.replay_session import ReplaySession
from ..app.replay_status import audit_complete
from ..app.replay_values import ReplayStep, ReplaySummary
from .geometry import window_size
from .primitives import Frame
from .replay_layout import replay_frame
from .window import GameWindow


def frame_for(step: ReplayStep, summary: ReplaySummary, width: int = 0, height: int = 0) -> Frame:
    """The picture for *step*, including the verdict its summary already reached.

    The size is passed through so every step of one replay is drawn into the
    window that is already open: a picture that resized itself between steps
    would make a grader think the board had changed.
    """
    return replay_frame(step, summary, audit_complete(summary), width, height)


def open_window(session: ReplaySession) -> GameWindow:
    """A window over *session*, already showing its first step and navigable."""
    summary = session.summary()
    first = session.first()
    width, height = window_size(first.grid_size)
    window = GameWindow(title=f"replay {summary.game_id}", width=width, height=height)

    def go(move: str) -> None:
        window.draw(frame_for(getattr(session, move)(), summary, width, height))

    window.draw(frame_for(first, summary, width, height))
    window.bind(
        {
            "<Right>": lambda: go("next"),
            "<Left>": lambda: go("previous"),
            "<Home>": lambda: go("first"),
            "<End>": lambda: go("last"),
        }
    )
    return window
