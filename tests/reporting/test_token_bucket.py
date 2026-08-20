"""The rule Appendix E rule 28 names, checked against the equation it states.

Ch 9 §9.3.2 writes it out: `tokens <- min(C, tokens + r*dt)`, `allow <=> tokens
>= 1`. These tests exercise that arithmetic directly, on an injected clock, so
nothing sleeps and every boundary is exact rather than approximately observed.
"""

import pytest
import report_fixtures as fix

from mars777_police.app.gatekeeper_bucket import TokenBucket


def bucket(capacity: float = 5.0, refill: float = 0.5) -> tuple[TokenBucket, fix.Clock]:
    clock = fix.Clock()
    return TokenBucket(capacity, refill, clock.monotonic), clock


def test_a_new_bucket_starts_full_exactly_as_the_source_example_does() -> None:
    held, _ = bucket()

    assert held.level == 5.0


def test_a_report_costs_exactly_one_whole_token() -> None:
    held, _ = bucket()

    held.stamp()

    assert held.level == 4.0


def test_a_full_bucket_admits_a_burst_of_exactly_its_capacity() -> None:
    held, _ = bucket()

    for _ in range(5):
        assert held.wait_seconds() == 0.0
        held.stamp()

    assert held.wait_seconds() > 0.0


def test_an_empty_bucket_asks_for_the_time_one_token_takes_to_refill() -> None:
    held, _ = bucket(capacity=1.0, refill=0.5)
    held.stamp()

    assert held.wait_seconds() == pytest.approx(2.0)


def test_refill_is_continuous_and_proportional_to_the_time_that_passed() -> None:
    held, clock = bucket(capacity=5.0, refill=0.5)
    for _ in range(5):
        held.stamp()

    clock.now += 4.0

    assert held.level == pytest.approx(2.0)


def test_refill_is_clamped_at_the_capacity_however_long_the_silence() -> None:
    held, clock = bucket(capacity=5.0, refill=0.5)
    held.stamp()

    clock.now += 100_000.0

    assert held.level == 5.0


def test_silence_is_rewarded_with_burst_capacity_and_never_with_more() -> None:
    held, clock = bucket(capacity=5.0, refill=0.5)
    for _ in range(5):
        held.stamp()

    clock.now += 6.0

    assert held.level == pytest.approx(3.0)


def test_the_level_never_goes_negative_however_often_it_is_spent() -> None:
    held, _ = bucket(capacity=1.0, refill=0.5)

    for _ in range(5):
        held.stamp()

    assert held.level >= 0.0


def test_a_bucket_delays_but_never_refuses_outright() -> None:
    held, _ = bucket(capacity=1.0, refill=0.5)
    held.stamp()

    assert held.check() is None


def test_a_bucket_that_could_never_admit_anything_is_refused_at_construction() -> None:
    clock = fix.Clock()

    with pytest.raises(ValueError, match="one token"):
        TokenBucket(0.5, 0.5, clock.monotonic)
    with pytest.raises(ValueError, match="never refills"):
        TokenBucket(5.0, 0.0, clock.monotonic)


def test_a_clock_that_moved_backwards_cannot_inflate_the_level() -> None:
    held, clock = bucket(capacity=5.0, refill=0.5)
    held.stamp()

    clock.now -= 1000.0

    assert held.level == 4.0
