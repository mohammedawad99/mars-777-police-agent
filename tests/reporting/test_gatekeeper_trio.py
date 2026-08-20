"""The three cumulative mechanisms Ch 9 §9.3.1 requires, and the order they run in.

The source's own figure sends an outgoing report through a Quota Manager, a
Token Bucket and a DOS Detector before it reaches the Gmail API, with a distinct
exit at each: `Rejected (quota full)`, `Blocked (no token)`, `LOCKED (anomaly)`.
These tests hold all three, and hold that no other operation gained any of them.
"""

import pytest
import report_fixtures as fix

from mars777_police.app.gatekeeper_admission import TOKEN_BUCKET, admission_for
from mars777_police.app.gatekeeper_bucket import TokenBucket
from mars777_police.app.gatekeeper_dos import DosDetector, ProviderLockedError
from mars777_police.app.gatekeeper_quota import DailyQuota, QuotaExhaustedError
from mars777_police.app.gatekeeper_windows import RollingWindows
from mars777_police.app.report_service import SEND_REPORT
from mars777_police.infra.rate_limit_file import load_rate_limits


def gmail_chain() -> object:
    clock = fix.Clock()
    return admission_for(load_rate_limits().policy_for(SEND_REPORT), clock.monotonic)


def test_the_shipped_gmail_policy_asks_for_the_token_bucket_by_name() -> None:
    policy = load_rate_limits().policy_for(SEND_REPORT)

    assert policy.admission == TOKEN_BUCKET
    assert policy.burst_capacity > 0
    assert policy.daily_quota > 0


def test_the_gmail_chain_is_the_three_mechanisms_in_the_source_s_order() -> None:
    kinds = [type(one) for one in gmail_chain().mechanisms]  # type: ignore[attr-defined]

    assert kinds == [DailyQuota, TokenBucket, DosDetector]


def test_every_other_operation_keeps_the_rolling_windows_unchanged() -> None:
    clock = fix.Clock()
    config = load_rate_limits()

    for operation in ("default", "ngrok.discover_tunnels"):
        chain = admission_for(config.policy_for(operation), clock.monotonic)
        assert [type(one) for one in chain.mechanisms] == [RollingWindows]


def test_the_refill_rate_is_the_configured_requests_per_minute_per_second() -> None:
    policy = load_rate_limits().policy_for(SEND_REPORT)
    bucket = gmail_chain().mechanisms[1]  # type: ignore[attr-defined]

    assert bucket.refill_per_second == pytest.approx(policy.requests_per_minute / 60.0)
    assert bucket.capacity == float(policy.burst_capacity)


def test_an_exhausted_daily_quota_refuses_rather_than_parking_a_caller() -> None:
    clock = fix.Clock()
    quota = DailyQuota(2, clock.monotonic)

    quota.stamp()
    quota.stamp()

    assert quota.remaining == 0
    assert quota.wait_seconds() == 0.0
    with pytest.raises(QuotaExhaustedError, match="daily quota"):
        quota.check()


def test_a_day_passing_restores_the_whole_allowance() -> None:
    clock = fix.Clock()
    quota = DailyQuota(2, clock.monotonic)
    quota.stamp()
    quota.stamp()

    clock.now += 86_401.0

    assert quota.remaining == 2
    assert quota.check() is None


def test_the_detector_latches_shut_on_a_burst_that_can_only_be_a_loop() -> None:
    clock = fix.Clock()
    detector = DosDetector(3, 60.0, clock.monotonic)

    for _ in range(4):
        detector.stamp()

    assert detector.locked is True
    with pytest.raises(ProviderLockedError, match="locked"):
        detector.check()


def test_the_lock_does_not_reopen_on_a_timer_because_the_defect_has_not_moved() -> None:
    clock = fix.Clock()
    detector = DosDetector(2, 60.0, clock.monotonic)
    for _ in range(3):
        detector.stamp()

    clock.now += 10_000.0

    with pytest.raises(ProviderLockedError):
        detector.check()


def test_a_calm_cadence_never_trips_the_detector() -> None:
    clock = fix.Clock()
    detector = DosDetector(3, 60.0, clock.monotonic)

    for _ in range(20):
        detector.stamp()
        clock.now += 61.0

    assert detector.locked is False
