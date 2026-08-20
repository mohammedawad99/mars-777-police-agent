"""The interactive window: one canvas, one panel, and keys that navigate.

The toolkit is the standard library's `tkinter`, and this is the only module
that drives it. It is obtained through `toolkit()` **when a window is built**
rather than imported at module scope, because `tkinter` is packaged separately
on Debian and Ubuntu and is genuinely absent from some ordinary Python 3.12
installations - including this project's own Linux CI. Everything about what to
draw was decided before this module ran, so a machine that cannot open a window
costs nothing but the window: the same frames render offscreen, and the
verification verdict is available headlessly either way.

**The window has no write path into the game.** It navigates a finished replay
and it reads the newest live snapshot; there is no control that can move an
agent, place a barrier or answer a claim.
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from . import palette
from .primitives import Frame
from .toolkit import toolkit

if TYPE_CHECKING:  # the names are for the type checker; the module is not needed to import
    import tkinter


@dataclass(slots=True)
class GameWindow:
    """A `tkinter` window that draws whatever frame it is handed."""

    title: str
    width: int
    height: int
    root: "tkinter.Tk" = field(init=False)
    canvas: "tkinter.Canvas" = field(init=False)

    def __post_init__(self) -> None:
        kit = toolkit()
        self.root = kit.Tk()
        self.root.title(self.title)
        self.root.minsize(self.width // 2, self.height // 2)
        self.canvas = kit.Canvas(
            self.root,
            width=self.width,
            height=self.height,
            bg=palette.BACKGROUND,
            highlightthickness=0,
        )
        self.canvas.pack(fill="both", expand=True)

    def draw(self, frame: Frame) -> None:
        """Replace everything on the canvas with *frame*."""
        self.canvas.delete("all")
        self.root.title(frame.title)
        for rect in frame.rects:
            self.canvas.create_rectangle(
                rect.left,
                rect.top,
                rect.right,
                rect.bottom,
                fill=rect.fill,
                outline=rect.outline or rect.fill,
            )
        for text in frame.texts:
            weight = "bold" if text.bold else "normal"
            self.canvas.create_text(
                text.left,
                text.top,
                text=text.value,
                fill=text.fill,
                anchor="nw",
                font=("TkFixedFont", text.size, weight),
            )
        self.canvas.update_idletasks()

    def bind(self, keys: dict[str, Callable[[], None]]) -> None:
        """Attach keyboard controls; each callback takes and returns nothing."""
        for key, action in keys.items():
            self.root.bind(key, lambda _event, run=action: run())  # type: ignore[misc]

    def run(self) -> None:  # pragma: no cover - blocks until a user closes it
        """Hand the process to the toolkit until the window is closed."""
        self.root.mainloop()

    def close(self) -> None:
        """Destroy the window and release the toolkit's resources."""
        self.root.destroy()
