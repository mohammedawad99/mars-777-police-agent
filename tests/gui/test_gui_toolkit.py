"""The real toolkit, on a machine that actually has one - and where it has none.

Everything else about the window is proved against recorders. This file is the
other half of that claim, in both directions:

* wherever a real toolkit and a real display exist, the same adapter drives the
  genuine widgets and draws the same frame;
* wherever the toolkit is simply **absent** - Debian and Ubuntu package it
  separately, and this project's own Linux CI has no `tkinter` - importing the
  graphical package still works, drawing to a file still works, and asking for a
  window produces a sentence with a remedy rather than a traceback.

Nothing here imports the toolkit at module scope, because that is exactly the
mistake it exists to prevent.
"""

import functools
from types import ModuleType

import gui_fixtures as fix
import pytest

from mars777_police.gui.image_renderer import render
from mars777_police.gui.live_layout import live_frame
from mars777_police.gui.toolkit import REMEDY, ToolkitMissingError, available, toolkit
from mars777_police.gui.window import GameWindow


@functools.cache
def can_open_a_window() -> bool:
    """Whether this machine has a toolkit **and** a display. Asked once."""
    if not available():
        return False
    kit = toolkit()
    try:
        root = kit.Tk()
    except kit.TclError:
        return False
    root.destroy()
    return True


needs_window = pytest.mark.skipif(
    not can_open_a_window(),
    reason="no window toolkit or no display; the offscreen renderer covers CI",
)


def test_the_package_draws_without_any_toolkit_at_all() -> None:
    """No skip, anywhere: this is the property that keeps CI able to run."""
    assert render(live_frame(fix.snapshot())).size[0] > 0


def test_asking_for_a_window_without_a_toolkit_names_what_to_install(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def missing(name: str) -> object:
        raise ModuleNotFoundError(f"No module named {name!r}")

    monkeypatch.setattr("importlib.import_module", missing)

    assert available() is False
    with pytest.raises(ToolkitMissingError, match="python3-tk"):
        toolkit()
    assert "--png" in REMEDY


def test_a_toolkit_that_imports_is_reported_present_and_handed_straight_back(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Asserted through a stand-in, so both answers are proved on any machine.

    Reading the real interpreter here would leave one branch unproved on
    whichever kind of machine happened to run the suite.
    """
    stand_in = ModuleType("tkinter")
    monkeypatch.setattr("importlib.import_module", lambda name: stand_in)

    assert available() is True
    assert toolkit() is stand_in


@needs_window
def test_the_real_window_draws_the_same_frame_the_recorders_saw() -> None:
    frame = live_frame(fix.snapshot(fix.belief((3, 3, "0.9"))))
    window = GameWindow("live", frame.width, frame.height)
    try:
        window.draw(frame)
        assert len(window.canvas.find_all()) == len(frame.rects) + len(frame.texts)
    finally:
        window.close()


@needs_window
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
