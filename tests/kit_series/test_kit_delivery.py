"""The at-least-once receiver contract, against the pinned decision table.

Every row below is the kit's, and every decision is ours. The distinction the
table exists to protect: a redelivery is **absorbed** and changes nothing, while
the same step under a *different* commit is an **equivocation** and stays loud -
a `(kind, step)` dedupe key would collapse the second silently into the first.
"""

import pytest
from kit_delivery_vectors import (
    ARRIVALS,
    NO_WINDOW_ARRIVAL,
    NO_WINDOW_DECISION,
    NO_WINDOW_STATE,
    STATE,
)

from mars777_police.app.kit_delivery import DeliveryDecision, DeliveryState, decide


def state(pinned: tuple[dict[int, str], int, int]) -> DeliveryState:
    played, window, expected = pinned
    return DeliveryState(dict(played), window, expected)


@pytest.mark.parametrize(("arrival", "expected", "note"), ARRIVALS)
def test_every_pinned_arrival_row_decides_the_way_the_kit_decides(
    arrival: tuple[int, str], expected: str, note: str
) -> None:
    step, commit = arrival

    assert decide(state(STATE), step, commit) is DeliveryDecision(expected)


def test_a_receiver_without_a_window_calls_an_ordinary_retry_race_a_violation() -> None:
    step, commit = NO_WINDOW_ARRIVAL

    assert decide(state(NO_WINDOW_STATE), step, commit) is DeliveryDecision(NO_WINDOW_DECISION)


def test_dedupe_is_on_the_commit_and_never_on_the_step_alone() -> None:
    """Collapsing these two into one decision is how tampering goes quiet."""
    held = state(STATE)

    assert decide(held, 2, "c2") is DeliveryDecision.ABSORB
    assert decide(held, 2, "cX") is DeliveryDecision.EQUIVOCATION


def test_the_window_is_the_only_flood_rule() -> None:
    """A second threshold beside the window would be unreachable by construction."""
    held = state(STATE)

    assert decide(held, held.expected + held.window, "c") is DeliveryDecision.BUFFER
    assert decide(held, held.expected + held.window + 1, "c") is DeliveryDecision.VIOLATION
