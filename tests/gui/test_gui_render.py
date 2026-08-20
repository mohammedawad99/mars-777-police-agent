"""The graphical output itself, produced where there is no screen at all.

This is what makes the GUI provable on Linux and Windows CI: the identical
`Frame` the window would draw is rasterised offscreen, so pixels can be asserted
without a display, a window manager or a human.
"""

from pathlib import Path

import gui_fixtures as fix
import pytest
from PIL import Image

from mars777_police.gui.image_renderer import render, write_png
from mars777_police.gui.live_layout import live_frame
from mars777_police.gui.palette import OWN


def rgb(colour: str) -> tuple[int, int, int]:
    """A hex colour as the triple the raster stores."""
    return (int(colour[1:3], 16), int(colour[3:5], 16), int(colour[5:7], 16))


def test_the_raster_is_exactly_the_size_the_frame_declared() -> None:
    frame = live_frame(fix.snapshot())
    image = render(frame)
    assert image.size == (frame.width, frame.height)
    assert image.mode == "RGB"


def test_our_own_cell_really_is_painted_where_the_layout_put_it() -> None:
    snapshot = fix.snapshot(own=(1, 1))
    frame = live_frame(snapshot)
    ours = next(rect for rect in frame.rects if rect.fill == OWN)
    image = render(frame)
    assert image.getpixel((ours.left + 2, ours.top + 2)) == rgb(OWN)


def test_the_same_snapshot_always_produces_the_same_pixels() -> None:
    once = render(live_frame(fix.snapshot(fix.belief((3, 3, "0.9")))))
    twice = render(live_frame(fix.snapshot(fix.belief((3, 3, "0.9")))))
    assert once.tobytes() == twice.tobytes()


def test_a_belief_map_changes_the_picture_a_belief_free_board_would_draw() -> None:
    plain = render(live_frame(fix.snapshot()))
    heated = render(live_frame(fix.snapshot(fix.belief((3, 3, "0.9")))))
    assert plain.tobytes() != heated.tobytes()


def test_writing_a_screenshot_creates_a_readable_png_of_the_right_size(
    tmp_path: Path,
) -> None:
    frame = live_frame(fix.snapshot())
    written = write_png(frame, tmp_path / "nested" / "live.png")
    assert written.exists()
    with Image.open(written) as reopened:
        assert reopened.format == "PNG"
        assert reopened.size == (frame.width, frame.height)


def test_rendering_needs_no_display_variable_at_all(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DISPLAY", raising=False)
    assert render(live_frame(fix.snapshot())).size[0] > 0


def test_a_board_with_no_rows_is_refused_rather_than_drawn_as_nothing() -> None:
    from mars777_police.gui.geometry import fit

    with pytest.raises(ValueError, match="at least one row"):
        fit(0, 800, 600)


def test_an_action_this_build_cannot_name_is_said_to_be_unknown() -> None:
    from mars777_police.app.action_words import UNKNOWN, action_label

    assert action_label(object()) == UNKNOWN  # type: ignore[arg-type]
