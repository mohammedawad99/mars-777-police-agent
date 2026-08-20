"""A viewer that misbehaves must cost the match nothing at all.

`PRD07-FR-008` requires GUI failure, slowness or disconnection to leave the game
running. These tests break the viewer in every way a viewer can break and check
that publication stays bounded, silent and one-way.
"""

import gui_fixtures as fix
import pytest

from mars777_police.app.live_view_feed import TURN, LiveViewFeed, action_label
from mars777_police.app.live_view_sink import NO_VIEWER, GuardedSink, LatestSnapshot
from mars777_police.app.turn_cursor import TurnCursor
from mars777_police.domain.actions import BarrierAction, MoveAction
from mars777_police.domain.board import Position
from mars777_police.domain.rules import Move


class Angry:
    """A viewer that raises on every snapshot it is offered."""

    def publish(self, snapshot: object) -> None:
        """Fail, loudly, every single time."""
        raise RuntimeError("the window fell over")


def test_a_raising_viewer_is_counted_and_never_reaches_the_caller() -> None:
    guarded = GuardedSink(Angry())
    for _ in range(3):
        guarded.publish(fix.snapshot())
    assert guarded.failures == 3


def test_the_box_holds_one_snapshot_however_many_turns_are_played() -> None:
    box = LatestSnapshot()
    for step in range(50):
        box.publish(fix.snapshot(step=step))
    assert box.published == 50
    assert box.dropped == 49
    taken = box.take()
    assert taken is not None and taken.step == 49


def test_reading_the_box_leaves_the_snapshot_for_the_next_reader() -> None:
    box = LatestSnapshot()
    box.publish(fix.snapshot())
    assert box.take() is box.take()


def test_an_empty_box_answers_nothing_rather_than_waiting() -> None:
    assert LatestSnapshot().take() is None


def test_publishing_to_nobody_is_a_single_call_that_returns() -> None:
    assert NO_VIEWER.publish(fix.snapshot()) is None


def test_the_feed_publishes_this_side_s_own_chosen_action_and_hint() -> None:
    box = LatestSnapshot()
    feed = LiveViewFeed(box, "POLICE", "MaRs-777-vs-peer")
    feed.show(fix.observation(), TurnCursor(2, 7), MoveAction(Move.N), "north of you")
    published = box.take()
    assert published is not None
    assert (published.sub_game, published.step, published.phase) == (2, 7, TURN)
    assert published.last_action == "MOVE N"
    assert published.hint == "north of you"


def test_a_feed_with_an_angry_viewer_still_returns_to_the_game() -> None:
    feed = LiveViewFeed(Angry(), "POLICE", "g")
    feed.show(fix.observation(), TurnCursor(1, 1), MoveAction(Move.STAY))
    assert feed.guard.failures == 1


@pytest.mark.parametrize(
    ("action", "expected"),
    [
        (MoveAction(Move.STAY), "MOVE STAY"),
        (MoveAction(Move.E), "MOVE E"),
        (BarrierAction(Position(4, 5)), "BARRIER 4,5"),
    ],
)
def test_the_status_line_names_our_own_action_and_nothing_else(
    action: object, expected: str
) -> None:
    assert action_label(action) == expected  # type: ignore[arg-type]
