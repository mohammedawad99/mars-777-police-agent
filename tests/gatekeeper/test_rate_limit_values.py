"""The local provider rate-limit policy, as a validated immutable value.

The excellence guideline §5.2 says every rate limit must come from a
configuration file and never from code, and §8.1 requires that file to carry its
own version starting at `1.00`. This is the value side of that: what a policy is,
what it refuses, and which versions this build can run.

**These are local provider limits.** They are not the peer-negotiated
`RateLimiterTerms`, not Appendix-F game configuration, and nothing here reaches
`config_sha256`, Step-0 or any artifact.
"""

import pytest

from mars777_police.shared.rate_limits import (
    SUPPORTED_RATE_LIMIT_VERSIONS,
    RateLimitConfig,
    RateLimitConfigError,
    RateLimitPolicy,
)


def policy(**changes: object) -> RateLimitPolicy:
    fields: dict[str, object] = {
        "requests_per_minute": 30,
        "requests_per_hour": 500,
        "concurrent_max": 2,
        "queue_depth": 100,
        "max_retries": 3,
        "retry_after_seconds": 5,
        "max_backoff_seconds": 60,
        "retryable_statuses": (429, 503),
    }
    fields.update(changes)
    return RateLimitPolicy(**fields)  # type: ignore[arg-type]


def test_this_build_supports_the_guideline_initial_version() -> None:
    assert frozenset({"1.00"}) == SUPPORTED_RATE_LIMIT_VERSIONS


def test_a_valid_policy_keeps_every_value_it_was_given() -> None:
    built = policy()

    assert built.requests_per_minute == 30
    assert built.concurrent_max == 2
    assert built.retryable_statuses == (429, 503)


@pytest.mark.parametrize(
    "field",
    ["requests_per_minute", "requests_per_hour", "concurrent_max", "queue_depth"],
)
def test_a_rate_or_capacity_of_zero_or_less_is_refused(field: str) -> None:
    """Zero would mean "never allow a call", which is a broken gate, not a policy."""
    for bad in (0, -1):
        with pytest.raises(RateLimitConfigError, match=field):
            policy(**{field: bad})


def test_a_negative_retry_budget_is_refused() -> None:
    with pytest.raises(RateLimitConfigError, match="max_retries"):
        policy(max_retries=-1)


def test_no_retries_is_a_legitimate_policy() -> None:
    """Zero is intentional here: some operations must never be repeated."""
    assert policy(max_retries=0).max_retries == 0


@pytest.mark.parametrize("field", ["retry_after_seconds", "max_backoff_seconds"])
def test_a_negative_wait_is_refused(field: str) -> None:
    with pytest.raises(RateLimitConfigError, match=field):
        policy(**{field: -1})


def test_a_backoff_cap_below_the_first_wait_is_refused() -> None:
    with pytest.raises(RateLimitConfigError, match="max_backoff_seconds"):
        policy(retry_after_seconds=30, max_backoff_seconds=10)


def test_a_non_integer_value_is_refused() -> None:
    with pytest.raises(RateLimitConfigError):
        policy(requests_per_minute="30")


def test_a_status_that_is_not_an_http_code_is_refused() -> None:
    with pytest.raises(RateLimitConfigError, match="retryable_statuses"):
        policy(retryable_statuses=(429, "503"))


def test_a_config_answers_with_the_named_policy_when_one_exists() -> None:
    named = policy(requests_per_minute=240)
    config = RateLimitConfig("1.00", policy(), {"ngrok.discover_tunnels": named})

    assert config.policy_for("ngrok.discover_tunnels") is named


def test_a_config_falls_back_to_its_default_for_an_unnamed_operation() -> None:
    fallback = policy()
    config = RateLimitConfig("1.00", fallback, {})

    assert config.policy_for("reporting.send_report") is fallback


def test_a_config_at_an_unsupported_version_cannot_exist() -> None:
    with pytest.raises(RateLimitConfigError, match=r"1\.99"):
        RateLimitConfig("1.99", policy(), {})


def test_the_version_is_the_string_the_guideline_writes() -> None:
    """`1.00` is stored as text: a JSON number would normalise it to `1.0`."""
    assert RateLimitConfig("1.00", policy(), {}).version == "1.00"


def test_a_status_list_that_is_not_a_tuple_is_refused() -> None:
    """The value object is immutable; a list would let a caller edit the policy."""
    with pytest.raises(RateLimitConfigError, match="tuple"):
        policy(retryable_statuses=[429])
