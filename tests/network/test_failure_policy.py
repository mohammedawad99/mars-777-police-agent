"""Retry classification: `FR-060`-`FR-065`, and the separation that matters.

The rule worth stating out loud is `FR-065` in both directions - a network
failure is never reported as an integrity failure, and an integrity failure is
never retried as though it were transient. A retry loop that swallowed
`E-AUTH-FAILURE` would turn a refused peer into a slow one.
"""

import pytest

from mars777_police.app.network_failure_policy import (
    FailureClass,
    RateLimitedError,
    classify,
    may_retry,
)
from mars777_police.app.protocol_errors import (
    AuthFailureError,
    ConfigMismatchError,
    ConventionMismatchError,
    LocalDefectError,
    MalformedMessageError,
    ReportDisagreeError,
    StaleMessageError,
)
from mars777_police.app.public_ingress import PublicIngressError

NEVER = [AuthFailureError, ConfigMismatchError, ConventionMismatchError, ReportDisagreeError]


@pytest.mark.parametrize("kind", NEVER)
def test_integrity_failures_are_never_retryable(kind: type[Exception]) -> None:
    failure = kind(kind.error_id)  # type: ignore[attr-defined]
    assert classify(failure) is FailureClass.NON_RETRYABLE
    assert not may_retry(failure)


def test_a_tunnel_failure_is_retryable_transport() -> None:
    failure = PublicIngressError("the tunnel died mid-turn")
    assert classify(failure) is FailureClass.RETRYABLE
    assert may_retry(failure)


def test_rate_limiting_is_paced_rather_than_immediately_retried() -> None:
    """`FR-061`: 429 waits for the next window; it is checked before transport."""
    failure = RateLimitedError("429")
    assert classify(failure) is FailureClass.PACED
    assert may_retry(failure)
    assert isinstance(failure, PublicIngressError)


@pytest.mark.parametrize("kind", [MalformedMessageError, StaleMessageError, LocalDefectError])
def test_other_peer_identities_block_rather_than_retry(kind: type[Exception]) -> None:
    failure = kind(kind.error_id)  # type: ignore[attr-defined]
    assert classify(failure) is FailureClass.BLOCKING
    assert not may_retry(failure)


def test_an_unrecognised_failure_is_never_retried_into_success() -> None:
    assert classify(RuntimeError("something else")) is FailureClass.NON_RETRYABLE
    assert not may_retry(RuntimeError("something else"))


def test_the_two_taxonomies_stay_disjoint() -> None:
    """`FR-065`: no transport failure lands in an integrity class, or the reverse."""
    assert classify(PublicIngressError("x")) is not FailureClass.NON_RETRYABLE
    assert classify(AuthFailureError("E-AUTH-FAILURE")) is not FailureClass.RETRYABLE
