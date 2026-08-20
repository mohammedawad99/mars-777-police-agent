"""Retrying, giving up, and the record each ending leaves behind.

A 429 is the case `REPORT-003` exists for, so it is pinned twice: the wait the
provider asked for is honoured when sane, and the number of attempts is bounded
by configuration rather than by how long the provider keeps saying no.
"""

import pytest
from test_gatekeeper import Clock, policy

from mars777_police.app.gatekeeper import Gatekeeper
from mars777_police.app.gatekeeper_events import CallOutcome
from mars777_police.app.gatekeeper_retry import ProviderStatusError
from mars777_police.shared.rate_limits import RateLimitConfig


def gate(clock: Clock, **changes: object) -> Gatekeeper:
    config = RateLimitConfig("1.00", policy(requests_per_minute=100, **changes), {})
    return Gatekeeper(config, monotonic=clock.monotonic, sleeper=clock.sleep)


def failing(times: int, failure: BaseException) -> object:
    """A call that fails *times* times and then answers."""
    seen: list[int] = []

    def run() -> str:
        seen.append(1)
        if len(seen) <= times:
            raise failure
        return "answer"

    return run


def test_a_retryable_status_is_repeated_until_it_succeeds() -> None:
    clock = Clock()
    keeper = gate(clock)

    answer = keeper.call("provider.op", failing(1, ProviderStatusError(429)))  # type: ignore[arg-type]

    assert answer == "answer"
    assert keeper.calls[-1].attempts == 2
    assert keeper.calls[-1].outcome is CallOutcome.SUCCEEDED


def test_the_wait_between_attempts_is_the_configured_backoff() -> None:
    clock = Clock()
    keeper = gate(clock)

    keeper.call("provider.op", failing(2, ProviderStatusError(503)))  # type: ignore[arg-type]

    assert clock.slept == [5.0, 10.0]


def test_a_retry_after_the_provider_asked_for_is_waited() -> None:
    clock = Clock()
    keeper = gate(clock)

    keeper.call("provider.op", failing(1, ProviderStatusError(429, retry_after=17.0)))  # type: ignore[arg-type]

    assert clock.slept == [17.0]


def test_an_absurd_retry_after_is_capped_by_configuration() -> None:
    clock = Clock()
    keeper = gate(clock)

    keeper.call("provider.op", failing(1, ProviderStatusError(429, retry_after=99999.0)))  # type: ignore[arg-type]

    assert clock.slept == [60.0]


def test_attempts_are_bounded_and_the_last_failure_is_raised() -> None:
    clock = Clock()
    keeper = gate(clock)

    with pytest.raises(ProviderStatusError):
        keeper.call("provider.op", failing(9, ProviderStatusError(429)))  # type: ignore[arg-type]

    assert keeper.calls[-1].attempts == 3
    assert keeper.calls[-1].outcome is CallOutcome.FAILED


def test_a_non_retryable_status_is_raised_at_once() -> None:
    clock = Clock()
    keeper = gate(clock)

    with pytest.raises(ProviderStatusError):
        keeper.call("provider.op", failing(9, ProviderStatusError(401)))  # type: ignore[arg-type]

    assert keeper.calls[-1].attempts == 1
    assert clock.slept == []


def test_a_transport_fault_is_repeated() -> None:
    clock = Clock()
    keeper = gate(clock)

    assert keeper.call("provider.op", failing(1, OSError("reset"))) == "answer"  # type: ignore[arg-type]


def test_a_policy_that_forbids_retries_raises_the_first_failure() -> None:
    clock = Clock()
    keeper = gate(clock, max_retries=0, retry_after_seconds=0, max_backoff_seconds=0)

    with pytest.raises(ProviderStatusError):
        keeper.call("provider.op", failing(1, ProviderStatusError(429)))  # type: ignore[arg-type]

    assert clock.slept == []


def test_the_ceiling_is_released_even_when_the_call_fails() -> None:
    clock = Clock()
    keeper = gate(clock, concurrent_max=1)

    with pytest.raises(ProviderStatusError):
        keeper.call("provider.op", failing(9, ProviderStatusError(401)))  # type: ignore[arg-type]

    assert keeper.call("provider.op", lambda: "after") == "after"


def test_no_observation_carries_provider_content() -> None:
    """The record is a shape, never a payload."""
    clock = Clock()
    keeper = gate(clock)
    secret = "out-of-band-provisioned-secret"

    keeper.call("provider.op", lambda: {"authtoken": secret})

    rendered = repr(keeper.calls)
    assert secret not in rendered
    assert "authtoken" not in rendered
