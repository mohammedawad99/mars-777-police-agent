"""What the two windows let a person do: look, and move the cursor. Nothing else.

The replay window navigates a finished sub-game; the live window watches one
being played. Neither has a control that reaches a decision, and these tests
check that by exercising every binding and every timer they install.
"""

from pathlib import Path

import gui_fixtures as fix
import gui_toolkit_doubles as toolkit
import pytest
import replay_fixtures as evidence

from mars777_police.app.live_view_sink import LatestSnapshot
from mars777_police.compose_replay import open_replay
from mars777_police.gui.live_app import REFRESH_MS
from mars777_police.gui.live_app import open_window as open_live
from mars777_police.gui.replay_app import open_window as open_replay_window
from mars777_police.gui.window import GameWindow


@pytest.fixture(autouse=True)
def headless(monkeypatch: pytest.MonkeyPatch) -> None:
    """The toolkit replaced by recorders, so this runs without a display."""
    toolkit.install(monkeypatch)


def words(window: GameWindow) -> str:
    """Everything the recorded canvas was actually asked to write."""
    canvas = window.canvas
    assert isinstance(canvas, toolkit.FakeCanvas)
    return " ".join(
        str(options.get("text", "")) for kind, _, options in canvas.items if kind == "text"
    )


def root_of(window: GameWindow) -> toolkit.FakeRoot:
    """The recorder standing in for this window's toolkit root."""
    found = window.root
    assert isinstance(found, toolkit.FakeRoot)
    return found


def test_the_replay_window_binds_exactly_the_four_movements_the_session_offers(
    tmp_path: Path,
) -> None:
    log, config = evidence.played(tmp_path)
    window = open_replay_window(open_replay(log, config, tmp_path))
    assert set(root_of(window).bindings) == {"<Right>", "<Left>", "<Home>", "<End>"}


def test_every_replay_key_redraws_and_none_of_them_changes_a_verdict(
    tmp_path: Path,
) -> None:
    log, config = evidence.played(tmp_path)
    session = open_replay(log, config, tmp_path)
    before = session.summary()
    window = open_replay_window(session)
    for key in ("<Right>", "<Left>", "<End>", "<Home>"):
        root_of(window).press(key)
        assert "REPLAY" in words(window)
    assert session.summary() == before


def test_the_live_window_opens_on_an_honest_waiting_picture_before_any_turn() -> None:
    window = open_live(LatestSnapshot(), "POLICE", "MaRs-777-vs-peer")
    assert "WAITING" in words(window)
    assert "MaRs-777-vs-peer" in words(window)


def test_the_live_window_polls_on_a_timer_and_never_blocks_the_game() -> None:
    box = LatestSnapshot()
    window = open_live(box, "POLICE", "g")
    root = root_of(window)
    assert root.timers[0][0] == REFRESH_MS
    box.publish(fix.snapshot(fix.belief((3, 3, "0.9"))))
    root.tick()
    assert "0.9" in words(window)
    assert len(root.timers) == 1, "the window rearmed itself"


def test_a_tick_with_an_empty_box_redraws_nothing_and_still_rearms() -> None:
    window = open_live(LatestSnapshot(), "POLICE", "g")
    root = root_of(window)
    before = words(window)
    root.tick()
    assert words(window) == before
    assert len(root.timers) == 1
