"""The one place a pushed turn waits, and what it is allowed to wake.

The symmetric-push wire means the opponent's turn arrives on our own inbound
server while the game loop is somewhere else entirely. This is the seam between
them, and its whole job is to make sure the loop is woken by exactly what it is
owed: an authoritative newly accepted message, never every HTTP arrival.

A tolerated duplicate proves the opponent is alive and discharges nothing, so it
must not wake the loop and must not renew its deadline - one clock per expected
message, so a stall burns the sender's budget rather than ours.
"""

import asyncio

import pytest
from kit_builders import kit_turn

from mars777_police.app.kit_inbox import KitTurnInbox
from mars777_police.app.protocol_errors import StaleMessageError


def inbox(window: int = 2, expected: int = 1) -> KitTurnInbox:
    return KitTurnInbox(window=window, expected=expected)


def turn(step: int, commit: str = "a") -> object:
    return kit_turn(step=step, commit=_digest(commit))


def _digest(seed: str) -> object:
    from mars777_police.app.protocol_values import Sha256Digest

    return Sha256Digest((seed * 64)[:64])


def test_the_next_expected_turn_is_applied_and_wakes_the_loop() -> None:
    held = inbox()

    applied = held.offer(turn(1))

    assert [one.step for one in applied] == [1]
    assert held.arrived.is_set()


def test_a_redelivery_is_absorbed_and_wakes_nothing() -> None:
    held = inbox()
    held.offer(turn(1))
    held.consume()

    applied = held.offer(turn(1))

    assert applied == ()
    assert held.arrived.is_set() is False


def test_the_same_step_under_a_different_commit_stays_loud() -> None:
    held = inbox()
    held.offer(turn(1))

    with pytest.raises(StaleMessageError):
        held.offer(turn(1, "b"))


def test_a_turn_inside_the_window_is_buffered_and_replayed_in_step_order() -> None:
    held = inbox()

    assert held.offer(turn(3)) == ()
    assert held.offer(turn(2)) == ()
    applied = held.offer(turn(1))

    assert [one.step for one in applied] == [1, 2, 3]


def test_a_buffered_turn_does_not_wake_the_loop_on_its_own() -> None:
    held = inbox()

    held.offer(turn(2))

    assert held.arrived.is_set() is False


def test_past_the_window_is_a_violation() -> None:
    held = inbox()

    with pytest.raises(StaleMessageError):
        held.offer(turn(4))


def test_a_step_below_the_frontier_that_never_played_is_discarded_silently() -> None:
    held = inbox(expected=3)
    held.played[1] = "x"

    assert held.offer(turn(2)) == ()


def test_the_buffer_is_bounded_by_the_window_and_by_nothing_else() -> None:
    """A second threshold beside the window would be unreachable by construction."""
    held = inbox()
    held.offer(turn(2))
    held.offer(turn(3))

    assert len(held.buffered) <= held.window


def test_waiting_returns_the_applied_turns_once_they_arrive() -> None:
    held = inbox()

    async def run() -> tuple[object, ...]:
        loop = asyncio.get_running_loop()
        loop.call_soon(held.offer, turn(1))
        return await held.take(5.0)

    assert [one.step for one in asyncio.run(run())] == [1]


def test_a_duplicate_never_renews_the_deadline() -> None:
    """Tolerated traffic proves liveness and discharges nothing that was owed."""
    held = inbox()
    held.offer(turn(1))
    held.consume()

    async def run() -> object:
        held.offer(turn(1))
        return await held.take(0.05)

    with pytest.raises(TimeoutError):
        asyncio.run(run())


def test_the_inbox_is_per_session_and_never_a_global() -> None:
    first, second = inbox(), inbox()
    first.offer(turn(1))

    assert second.arrived.is_set() is False
    assert second.expected == 1
