"""Which provider failures may be repeated, and how long to wait first.

`REPORT-003` and Appendix E rule 28 exist for one reason: repeating a call after
a 429 risks the sending account. So the classification here is deliberately
narrow - a status the **policy** names, or a transport fault - and everything
else is an answer rather than weather. A malformed request, an authentication
failure and a semantic 4xx are never repeated.

**The wait is ours, not the provider's.** A `Retry-After` is honoured when it is
sane, but always clamped to the configured maximum: a provider that asked us to
sleep for a day would otherwise stop the process by saying so. Backoff is plain
exponential from the configured first wait, doubling to the same cap.

**No jitter.** Randomness here would buy dispersion this project has no use for -
there is one client, not a fleet - at the price of tests that cannot pin a wait.
"""

from ..shared.rate_limits import RateLimitPolicy


class ProviderCallError(Exception):
    """A failure the gate is allowed to see and classify."""


class ProviderStatusError(ProviderCallError):
    """A provider answered with an HTTP status the caller could not use."""

    def __init__(self, status: int, retry_after: float | None = None) -> None:
        super().__init__(f"provider answered {status}")
        self.status: int = status
        self.retry_after: float | None = retry_after


def would_retry(policy: RateLimitPolicy, failure: BaseException) -> bool:
    """Whether *failure* may be repeated under *policy*."""
    if policy.max_retries <= 0:
        return False
    if isinstance(failure, ProviderStatusError):
        return failure.status in policy.retryable_statuses
    return isinstance(failure, OSError)


def wait_before_retry(policy: RateLimitPolicy, failure: BaseException, attempt: int) -> float:
    """Return the seconds to wait before attempt *attempt* + 1, never unbounded."""
    cap = float(policy.max_backoff_seconds)
    asked = failure.retry_after if isinstance(failure, ProviderStatusError) else None
    if asked is not None and asked > 0:
        return min(float(asked), cap)
    backoff = float(policy.retry_after_seconds) * float(2 ** max(attempt - 1, 0))
    return min(backoff, cap)
