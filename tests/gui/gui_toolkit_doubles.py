"""A toolkit that records instead of drawing, so the window is testable anywhere.

CI has no display, and a window is exactly the part of a graphical program that
usually goes untested for that reason. These doubles stand in for `tkinter.Tk`
and `tkinter.Canvas` so every line of the window adapter runs on Linux, on
Windows and in a headless container - and so a test can read back what was
drawn instead of photographing a screen.
"""

from collections.abc import Callable
from typing import Any


class FakeCanvas:
    """Records every shape it is asked for, and forgets them on `delete`."""

    def __init__(self, master: object, **options: object) -> None:
        self.master = master
        self.options = options
        self.items: list[tuple[str, tuple[object, ...], dict[str, object]]] = []
        self.packed = False
        self.updates = 0

    def pack(self, **options: object) -> None:
        """Accept placement. Nothing is laid out because nothing is shown."""
        self.packed = True

    def create_rectangle(self, *box: object, **options: object) -> int:
        """Record one rectangle."""
        self.items.append(("rectangle", box, options))
        return len(self.items)

    def create_text(self, *where: object, **options: object) -> int:
        """Record one piece of text."""
        self.items.append(("text", where, options))
        return len(self.items)

    def delete(self, which: str) -> None:
        """Clear the canvas, exactly as the real widget does for `"all"`."""
        assert which == "all"
        self.items.clear()

    def update_idletasks(self) -> None:
        """Count the flush the window asks for after every draw."""
        self.updates += 1

    def find_all(self) -> tuple[int, ...]:
        """Every recorded item, in the order it was created."""
        return tuple(range(1, len(self.items) + 1))


class FakeRoot:
    """A window that remembers its title, its bindings and its timers."""

    def __init__(self) -> None:
        self.titles: list[str] = []
        self.bindings: dict[str, Callable[[Any], None]] = {}
        self.timers: list[tuple[int, Callable[[], None]]] = []
        self.minsize_called: tuple[int, int] | None = None
        self.destroyed = False
        self.looped = 0

    def title(self, value: str) -> None:
        """Record the title the window was given."""
        self.titles.append(value)

    def minsize(self, width: int, height: int) -> None:
        """Record the floor the window declared."""
        self.minsize_called = (width, height)

    def bind(self, sequence: str, handler: Callable[[Any], None]) -> None:
        """Record one keyboard binding."""
        self.bindings[sequence] = handler

    def after(self, milliseconds: int, handler: Callable[[], None]) -> str:
        """Record one timer without ever firing it."""
        self.timers.append((milliseconds, handler))
        return f"timer{len(self.timers)}"

    def mainloop(self) -> None:
        """Return at once: a test must never hand over its thread."""
        self.looped += 1

    def destroy(self) -> None:
        """Record that the window was closed."""
        self.destroyed = True

    def press(self, sequence: str) -> None:
        """Deliver one key to whatever the window bound to it."""
        self.bindings[sequence](object())

    def tick(self) -> None:
        """Fire the timer that is currently pending, exactly once."""
        _, handler = self.timers.pop()
        handler()


def install(monkeypatch: Any) -> list[FakeRoot]:
    """Replace the toolkit inside the window adapter; return the roots created."""
    from mars777_police.gui import window

    made: list[FakeRoot] = []

    def build() -> FakeRoot:
        made.append(FakeRoot())
        return made[-1]

    monkeypatch.setattr(window.tkinter, "Tk", build)
    monkeypatch.setattr(window.tkinter, "Canvas", FakeCanvas)
    return made
