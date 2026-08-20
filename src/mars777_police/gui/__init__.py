"""`mars777_police.gui` - the graphical surface, and the only place a toolkit lives.

Two windows over one model. `live_layout` draws what `GUI-001` permits while a
match is being played; `replay_layout` draws a finished sub-game, where
`PRD07-FR-023` finally allows both agents' true paths to be seen. Both produce a
`Frame`, a plain value made of rectangles and text.

**A `Frame` is the whole contract between deciding and drawing.** `window` hands
it to `tkinter`; `image_renderer` rasterises the identical value with no display
at all, which is what lets the graphical output be asserted on Linux and Windows
CI and what produces the submission screenshots. Nothing in this package reads
game state, and nothing in it can be reached from a decision.
"""

from .geometry import BoardGeometry, fit, window_size
from .image_renderer import render, write_png
from .live_layout import BELIEF_LABEL, live_frame
from .primitives import Frame, Rect, Text
from .replay_layout import OFFICIAL, REPLAY, replay_frame
from .toolkit import ToolkitMissingError, available

__all__ = [
    "BELIEF_LABEL",
    "OFFICIAL",
    "REPLAY",
    "BoardGeometry",
    "Frame",
    "Rect",
    "Text",
    "ToolkitMissingError",
    "available",
    "fit",
    "live_frame",
    "render",
    "replay_frame",
    "window_size",
    "write_png",
]
