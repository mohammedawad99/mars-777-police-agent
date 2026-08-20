"""The window adapter itself: what it draws, what it binds, and what it cannot do.

The stage prohibition list is the point of this file. There is no movement
button, no barrier chooser, no editable belief, no hint override and no "force
capture" - so what a key can reach is checked here, against the real adapter.
"""

import gui_fixtures as fix
import gui_toolkit_doubles as toolkit
import pytest

from mars777_police.gui.live_layout import live_frame
from mars777_police.gui.window import GameWindow


@pytest.fixture
def roots(monkeypatch: pytest.MonkeyPatch) -> list[toolkit.FakeRoot]:
    """The toolkit replaced by recorders, so this runs without a display."""
    return toolkit.install(monkeypatch)


def test_the_window_draws_every_rectangle_and_every_word_of_its_frame(
    roots: list[toolkit.FakeRoot],
) -> None:
    frame = live_frame(fix.snapshot(fix.belief((3, 3, "0.9"))))
    window = GameWindow("live", frame.width, frame.height)
    window.draw(frame)
    kinds = [kind for kind, _, _ in window.canvas.items]  # type: ignore[union-attr]
    assert kinds.count("rectangle") == len(frame.rects)
    assert kinds.count("text") == len(frame.texts)


def test_redrawing_replaces_the_picture_rather_than_stacking_on_it(
    roots: list[toolkit.FakeRoot],
) -> None:
    frame = live_frame(fix.snapshot())
    window = GameWindow("live", frame.width, frame.height)
    window.draw(frame)
    first = len(window.canvas.items)  # type: ignore[union-attr]
    window.draw(frame)
    assert len(window.canvas.items) == first  # type: ignore[union-attr]


def test_the_title_follows_the_frame_so_a_mode_is_never_mislabelled(
    roots: list[toolkit.FakeRoot],
) -> None:
    frame = live_frame(fix.snapshot())
    GameWindow("placeholder", frame.width, frame.height).draw(frame)
    assert roots[0].titles == ["placeholder", frame.title]


def test_a_bound_key_takes_no_argument_so_it_cannot_carry_an_instruction(
    roots: list[toolkit.FakeRoot],
) -> None:
    pressed: list[str] = []
    window = GameWindow("live", 400, 300)
    window.bind({"<Right>": lambda: pressed.append("right")})
    roots[0].press("<Right>")
    assert pressed == ["right"]


def test_closing_the_window_destroys_it_and_nothing_else(
    roots: list[toolkit.FakeRoot],
) -> None:
    window = GameWindow("live", 400, 300)
    window.close()
    assert roots[0].destroyed is True


def test_running_the_window_hands_over_only_the_toolkit_loop(
    roots: list[toolkit.FakeRoot],
) -> None:
    GameWindow("live", 400, 300).run()
    assert roots[0].looped == 1
