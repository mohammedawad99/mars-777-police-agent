"""The bounded handoff between two role backends, and what it refuses.

The pinned peer greets for the next sub-game the moment it has settled the
previous one, so a greeting for `n+1` can arrive while `n` is still draining its
audits. Acknowledging it into a queue nobody drains is the hazard the kit's own
docs warn about: the opponent burns its whole connect budget on a message we
said `ok` to and never acted on.

So the handoff has three explicit states, and a greeting is acknowledged only
once it has actually been assigned to the backend that will play it.
"""

import asyncio

import pytest

from mars777_police.app.kit_handoff import HandoffPhase, SeriesHandoff
from mars777_police.app.kit_messages import KitRole
from mars777_police.app.protocol_errors import StaleMessageError


def handoff() -> SeriesHandoff:
    return SeriesHandoff(KitRole.POLICE)


def test_a_series_opens_active_on_its_first_sub_game() -> None:
    held = handoff()

    assert held.sub_game == 1
    assert held.phase is HandoffPhase.ACTIVE
    assert held.role is KitRole.POLICE


def test_the_role_follows_the_schedule_and_nothing_else() -> None:
    held = handoff()
    held.begin_settlement()
    held.settled()
    held.open(2)

    assert held.sub_game == 2
    assert held.role is KitRole.THIEF


def test_gameplay_may_not_move_on_before_the_backend_says_it_settled() -> None:
    """Settlement is signalled, never inferred from HTTP silence."""
    held = handoff()

    with pytest.raises(StaleMessageError):
        held.open(2)


def test_a_next_greeting_is_not_assignable_until_the_previous_game_settled() -> None:
    held = handoff()

    assert held.assignable(2) is False
    held.begin_settlement()
    assert held.assignable(2) is False
    held.settled()
    assert held.assignable(2) is True


def test_the_current_sub_game_stays_assignable_for_a_redelivered_greeting() -> None:
    """A duplicate greeting must not create a second backend or a second series."""
    held = handoff()

    assert held.assignable(1) is True
    held.open(1)
    assert held.sub_game == 1


def test_a_greeting_for_a_game_that_is_not_next_is_refused() -> None:
    held = handoff()
    held.begin_settlement()
    held.settled()

    with pytest.raises(StaleMessageError):
        held.open(4)


def test_waiting_for_the_next_game_is_bounded_and_released_by_settlement() -> None:
    held = handoff()

    async def run() -> int:
        loop = asyncio.get_running_loop()
        loop.call_soon(lambda: (held.begin_settlement(), held.settled()))
        await held.await_assignable(2, 5.0)
        return held.sub_game

    assert asyncio.run(run()) == 1


def test_a_greeting_that_never_becomes_assignable_times_out_rather_than_acking() -> None:
    held = handoff()

    with pytest.raises(TimeoutError):
        asyncio.run(held.await_assignable(2, 0.05))


def test_the_series_ends_after_its_sixth_sub_game() -> None:
    held = handoff()
    for number in range(2, 7):
        held.begin_settlement()
        held.settled()
        held.open(number)

    assert held.sub_game == 6
    held.begin_settlement()
    held.settled()
    with pytest.raises(StaleMessageError):
        held.open(7)
