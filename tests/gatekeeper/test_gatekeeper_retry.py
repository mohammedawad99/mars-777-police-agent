"""Which provider failures may be repeated, and how long the gate waits first.

`REPORT-003` and Appendix E rule 28 are about one thing: a blind retry after a
429 risks the sending account. So the classification is deliberately narrow -
a status the policy names, or a transport fault - and the wait is bounded by
configuration, never by whatever the provider asked for.
"""

from mars777_police.app.gatekeeper_retry import (
    ProviderCallError,
    ProviderStatusError,
    wait_before_retry,
    would_retry,
)
from mars777_police.shared.rate_limits import RateLimitPolicy

POLICY = RateLimitPolicy(
    requests_per_minute=30,
    requests_per_hour=500,
    concurrent_max=2,
    queue_depth=10,
    max_retries=3,
    retry_after_seconds=5,
    max_backoff_seconds=60,
    retryable_statuses=(429, 503),
)


def test_a_status_the_policy_names_is_retryable() -> None:
    assert would_retry(POLICY, ProviderStatusError(429)) is True
    assert would_retry(POLICY, ProviderStatusError(503)) is True


def test_a_status_the_policy_does_not_name_is_not_retryable() -> None:
    """Semantic and authentication failures are answers, not weather."""
    for status in (400, 401, 403, 404, 422):
        assert would_retry(POLICY, ProviderStatusError(status)) is False


def test_a_transport_fault_is_retryable() -> None:
    assert would_retry(POLICY, OSError("connection reset")) is True


def test_anything_else_is_not_retryable() -> None:
    assert would_retry(POLICY, ValueError("malformed request")) is False


def test_a_policy_that_forbids_retries_never_retries() -> None:
    never = RateLimitPolicy(
        requests_per_minute=30,
        requests_per_hour=500,
        concurrent_max=1,
        queue_depth=1,
        max_retries=0,
        retry_after_seconds=0,
        max_backoff_seconds=0,
        retryable_statuses=(),
    )

    assert would_retry(never, ProviderStatusError(429)) is False
    assert would_retry(never, OSError()) is False


def test_the_first_wait_is_the_configured_backoff() -> None:
    assert wait_before_retry(POLICY, ProviderStatusError(503), attempt=1) == 5.0


def test_the_wait_doubles_with_each_attempt() -> None:
    waits = [wait_before_retry(POLICY, ProviderStatusError(503), attempt=n) for n in (1, 2, 3)]

    assert waits == [5.0, 10.0, 20.0]


def test_the_wait_is_capped_by_configuration() -> None:
    assert wait_before_retry(POLICY, ProviderStatusError(503), attempt=9) == 60.0


def test_a_retry_after_the_provider_asked_for_is_honoured() -> None:
    assert wait_before_retry(POLICY, ProviderStatusError(429, retry_after=12.0), attempt=1) == 12.0


def test_an_absurd_retry_after_is_capped_rather_than_obeyed() -> None:
    """A provider must not be able to make this process sleep for a day."""
    asked = ProviderStatusError(429, retry_after=86400.0)

    assert wait_before_retry(POLICY, asked, attempt=1) == 60.0


def test_a_negative_retry_after_falls_back_to_the_configured_backoff() -> None:
    assert wait_before_retry(POLICY, ProviderStatusError(429, retry_after=-3.0), attempt=1) == 5.0


def test_a_transport_fault_uses_the_configured_backoff() -> None:
    assert wait_before_retry(POLICY, OSError(), attempt=2) == 10.0


def test_a_status_error_reports_what_it_was() -> None:
    failure = ProviderStatusError(429, retry_after=7.0)

    assert failure.status == 429
    assert failure.retry_after == 7.0
    assert isinstance(failure, ProviderCallError)
    assert "429" in str(failure)
