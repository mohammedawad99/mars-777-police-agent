"""The gate itself: rate, concurrency, backpressure, retries and what it records.

Time is injected everywhere. A test that slept for a real backoff would be slow
and, worse, would prove nothing about the interval it claims to pin.
"""

import pytest

from mars777_police.app.gatekeeper import (
    ConcurrencyExceededError,
    Gatekeeper,
    GatekeeperRejectedError,
)
from mars777_police.app.gatekeeper_events import CallOutcome
from mars777_police.shared.rate_limits import RateLimitConfig, RateLimitPolicy


class Clock:
    """A monotonic clock a test moves on purpose, and the sleeper that moves it."""

    def __init__(self) -> None:
        self.now = 1000.0
        self.slept: list[float] = []

    def monotonic(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.slept.append(seconds)
        self.now += seconds


def policy(**changes: object) -> RateLimitPolicy:
    fields: dict[str, object] = {
        "requests_per_minute": 3,
        "requests_per_hour": 100,
        "concurrent_max": 1,
        "queue_depth": 2,
        "max_retries": 2,
        "retry_after_seconds": 5,
        "max_backoff_seconds": 60,
        "retryable_statuses": (429, 503),
    }
    fields.update(changes)
    return RateLimitPolicy(**fields)  # type: ignore[arg-type]


def gate(clock: Clock, **changes: object) -> Gatekeeper:
    config = RateLimitConfig("1.00", policy(**changes), {})
    return Gatekeeper(config, monotonic=clock.monotonic, sleeper=clock.sleep)


def test_a_call_under_the_limit_runs_immediately() -> None:
    clock = Clock()

    assert gate(clock).call("provider.op", lambda: "answer") == "answer"
    assert clock.slept == []


def test_the_minute_window_delays_the_call_that_exceeds_it() -> None:
    clock = Clock()
    keeper = gate(clock)
    for _ in range(3):
        keeper.call("provider.op", lambda: None)

    keeper.call("provider.op", lambda: None)

    assert clock.slept == [60.0]


def test_the_hour_window_is_watched_as_well_as_the_minute() -> None:
    clock = Clock()
    keeper = gate(clock, requests_per_minute=10, requests_per_hour=2)
    keeper.call("provider.op", lambda: None)
    keeper.call("provider.op", lambda: None)

    keeper.call("provider.op", lambda: None)

    assert clock.slept == [3600.0]


def test_a_throttled_call_is_recorded_as_queued_and_throttled() -> None:
    clock = Clock()
    keeper = gate(clock)
    for _ in range(4):
        keeper.call("provider.op", lambda: None)

    assert keeper.calls[-1].queued is True
    assert keeper.calls[-1].throttled is True
    assert keeper.calls[0].queued is False


def test_each_operation_has_its_own_windows() -> None:
    clock = Clock()
    keeper = gate(clock)
    for _ in range(3):
        keeper.call("provider.first", lambda: None)

    keeper.call("provider.second", lambda: None)

    assert clock.slept == []


def test_the_concurrency_ceiling_refuses_a_re_entrant_call() -> None:
    clock = Clock()
    keeper = gate(clock)

    def nested() -> None:
        keeper.call("provider.op", lambda: None)

    with pytest.raises(ConcurrencyExceededError, match=r"provider\.op"):
        keeper.call("provider.op", nested)

    assert keeper.calls[0].outcome is CallOutcome.REFUSED


def test_a_higher_ceiling_admits_the_nested_call() -> None:
    clock = Clock()
    keeper = gate(clock, concurrent_max=2)

    assert (
        keeper.call("provider.op", lambda: keeper.call("provider.op", lambda: "inner")) == "inner"
    )


def test_a_full_waiting_room_is_backpressure_not_a_silent_drop() -> None:
    """A second caller arriving while the first is still waiting is refused.

    The sleeper is the seam: it is what runs while a caller waits, so a sleeper
    that makes its own gated call is exactly "somebody else arrived meanwhile",
    modelled without a thread and without a real interval.
    """
    clock = Clock()
    keeper = gate(clock, concurrent_max=3, queue_depth=1, requests_per_minute=1)
    arrivals: list[Exception] = []

    def meanwhile(seconds: float) -> None:
        clock.sleep(seconds)
        if len(arrivals) < 1:
            try:
                keeper.call("provider.op", lambda: None)
            except GatekeeperRejectedError as refused:
                arrivals.append(refused)

    keeper.sleeper = meanwhile
    keeper.call("provider.op", lambda: None)
    keeper.call("provider.op", lambda: None)

    assert len(arrivals) == 1
    assert any(call.outcome is CallOutcome.REJECTED for call in keeper.calls)


def test_a_rejected_call_never_runs() -> None:
    clock = Clock()
    keeper = gate(clock, concurrent_max=3, queue_depth=1, requests_per_minute=1)
    ran: list[str] = []

    def meanwhile(seconds: float) -> None:
        clock.sleep(seconds)
        if not ran:
            ran.append("attempted")
            with pytest.raises(GatekeeperRejectedError):
                keeper.call("provider.op", lambda: ran.append("executed"))

    keeper.sleeper = meanwhile
    keeper.call("provider.op", lambda: None)
    keeper.call("provider.op", lambda: None)

    assert ran == ["attempted"]
