"""What the live picture must say, and what it must never contain.

Reading a `Frame` is reading exactly what a viewer would see, so these are the
`GUI-002` tests: not "the code does not fetch an opponent cell", but "no
rectangle and no word on the finished picture is one".
"""

import gui_fixtures as fix

from mars777_police.app.live_view_values import LIVE
from mars777_police.gui.geometry import fit
from mars777_police.gui.live_layout import BELIEF_LABEL, live_frame
from mars777_police.gui.palette import BARRIER, OWN


def test_the_banner_names_the_mode_the_role_and_the_turn_state() -> None:
    words = " ".join(live_frame(fix.snapshot()).labels())
    assert LIVE in words
    assert "POLICE" in words
    assert "step 3" in words
    assert "TURN" in words


def test_the_picture_says_it_is_local_truth_and_that_the_opponent_is_not_shown() -> None:
    words = live_frame(fix.snapshot()).labels()
    assert "LOCAL TRUTH ONLY" in words
    assert "opponent position: never shown" in words


def test_the_belief_map_is_labelled_an_estimate_rather_than_a_sighting() -> None:
    frame = live_frame(fix.snapshot(fix.belief((3, 3, "0.9"))))
    assert BELIEF_LABEL in frame.labels()
    assert "not a sighting" in BELIEF_LABEL


def test_every_believed_cell_carries_its_own_number_beside_its_shade() -> None:
    frame = live_frame(fix.snapshot(fix.belief((3, 3, "0.9"), (4, 1, "0.25"))))
    assert "0.9" in frame.labels()
    assert "0.25" in frame.labels()


def test_exactly_one_cell_is_painted_as_ours_and_it_is_the_one_we_hold() -> None:
    snapshot = fix.snapshot()
    frame = live_frame(snapshot)
    geometry = fit(snapshot.grid_size, frame.width, frame.height)
    left, top, _, _ = geometry.cell_box(*snapshot.own_cell)
    ours = [rect for rect in frame.rects if rect.fill == OWN]
    assert len(ours) == 1
    assert (ours[0].left, ours[0].top) == (left, top)
    assert "ME" in frame.labels()


def test_only_the_barriers_the_observation_carried_are_drawn() -> None:
    snapshot = fix.snapshot()
    frame = live_frame(snapshot)
    drawn = [rect for rect in frame.rects if rect.fill == BARRIER]
    assert len(drawn) == len(snapshot.barriers) == 2


def test_a_belief_free_sub_game_draws_nothing_beyond_what_it_was_told() -> None:
    snapshot = fix.snapshot()
    frame = live_frame(snapshot)
    chrome = 3  # the background, the banner and the side panel
    grid = snapshot.grid_size * snapshot.grid_size
    assert len(frame.rects) == chrome + grid + len(snapshot.barriers) + 1


def test_the_picture_scales_to_the_window_it_is_given() -> None:
    small = live_frame(fix.snapshot(), 700, 520)
    assert (small.width, small.height) == (700, 520)
