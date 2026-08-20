"""The bounded FIFO a rate-limited caller waits in.

Guideline §5.3: when the limits are reached the gate **queues** rather than
rejecting or crashing - FIFO, a depth from configuration, backpressure when it
is full, and a drain that serves waiters as the windows reset. Rejection is what
happens at the boundary, not instead of the queue.
"""

import pytest

from mars777_police.app.gatekeeper_queue import RateWindowQueue, WaitingRoomFullError


def test_a_new_queue_is_empty() -> None:
    assert RateWindowQueue(3).depth == 0


def test_joining_returns_a_ticket_and_grows_the_depth() -> None:
    room = RateWindowQueue(3)

    first = room.join()

    assert room.depth == 1
    assert first == room.head


def test_tickets_are_served_in_arrival_order() -> None:
    room = RateWindowQueue(3)

    first, second, third = room.join(), room.join(), room.join()

    assert [first, second, third] == sorted([third, second, first])
    assert room.head == first


def test_only_the_head_may_proceed() -> None:
    room = RateWindowQueue(3)
    first, second = room.join(), room.join()

    assert room.turn_of(first) is True
    assert room.turn_of(second) is False


def test_serving_the_head_promotes_the_next_arrival() -> None:
    room = RateWindowQueue(3)
    first, second = room.join(), room.join()

    room.serve(first)

    assert room.head == second
    assert room.depth == 1


def test_a_full_waiting_room_refuses_rather_than_growing() -> None:
    room = RateWindowQueue(2)
    room.join()
    room.join()

    with pytest.raises(WaitingRoomFullError, match="2"):
        room.join()


def test_leaving_frees_the_place_for_the_next_arrival() -> None:
    """A cancelled caller must not hold a place it will never use."""
    room = RateWindowQueue(2)
    first, second = room.join(), room.join()

    room.leave(first)

    assert room.depth == 1
    assert room.head == second
    assert room.join() != second


def test_a_cancellation_in_the_middle_does_not_reorder_the_rest() -> None:
    room = RateWindowQueue(4)
    first, second, third = room.join(), room.join(), room.join()

    room.leave(second)

    assert room.head == first
    room.serve(first)
    assert room.head == third


def test_leaving_twice_is_safe() -> None:
    room = RateWindowQueue(2)
    ticket = room.join()

    room.leave(ticket)
    room.leave(ticket)

    assert room.depth == 0


def test_the_head_of_an_empty_room_is_nothing() -> None:
    assert RateWindowQueue(2).head is None


def test_a_waiting_room_needs_room_to_wait_in() -> None:
    with pytest.raises(ValueError, match="depth"):
        RateWindowQueue(0)
