"""The real toolkit, on a machine that actually has a screen.

Everything else about the window is proved against recorders, because a CI
runner has no display. This file is the other half of that claim: wherever a
display exists, the same adapter drives the genuine `tkinter` widgets and draws
the same frame.

**Skipped by probe, not by platform.** Whether a window can open is a property of
the machine, not of the operating system name, so it is answered by trying once
rather than by guessing from `sys.platform`. A missing screen is not a defect.
"""

import functools
import tkinter

import gui_fixtures as fix
import pytest

from mars777_police.gui.live_layout import live_frame
from mars777_police.gui.window import GameWindow


@functools.cache
def has_display() -> bool:
    """Whether this machine can actually open a window. Asked once."""
    try:
        root = tkinter.Tk()
    except tkinter.TclError:
        return False
    root.destroy()
    return True


needs_display = pytest.mark.skipif(
    not has_display(),
    reason="the interactive toolkit needs a display; the offscreen renderer covers CI",
)


def test_the_toolkit_this_project_depends_on_is_importable_everywhere() -> None:
    """No skip: importing the toolkit must work even where no window can open."""
    assert hasattr(tkinter, "Tk")
    assert hasattr(tkinter, "Canvas")


@needs_display
def test_the_real_window_draws_the_same_frame_the_recorders_saw() -> None:
    frame = live_frame(fix.snapshot(fix.belief((3, 3, "0.9"))))
    window = GameWindow("live", frame.width, frame.height)
    try:
        window.draw(frame)
        assert len(window.canvas.find_all()) == len(frame.rects) + len(frame.texts)
    finally:
        window.close()


@needs_display
def test_the_real_toolkit_accepts_the_bindings_the_replay_window_asks_for() -> None:
    """Registered with the genuine widget, not merely recorded by a double.

    Asserted through `bind()`'s own registry rather than by synthesising a key
    press: delivering an event needs input focus, which a headless or unfocused
    session cannot promise, and a test that depends on window-manager behaviour
    would be flaky rather than thorough.
    """
    window = GameWindow("live", 400, 300)
    try:
        window.bind({"<Right>": lambda: None, "<Left>": lambda: None})
        assert set(window.root.bind()) >= {"<Key-Right>", "<Key-Left>"}
    finally:
        window.close()
