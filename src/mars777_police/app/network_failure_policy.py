"""Which failures may be retried, and which must never be.

`PRD05-FR-060`-`FR-065` split connectivity outcomes into four classes, and the
one that matters most is the separation `FR-065` states in both directions: a
network failure must not be reported as an integrity failure, and an integrity
failure must not be retried as though it were a network problem. A retry loop
that swallowed `E-AUTH-FAILURE` would convert a refused peer into a slow one.

Classification is **by the failure's own type**, not by a message, so a renamed
string cannot silently move a failure between classes.
"""

from enum import StrEnum

from .protocol_errors import (
    AuthFailureError,
    ConfigMismatchError,
    ConventionMismatchError,
    PeerProtocolError,
    ReportDisagreeError,
)
from .public_ingress import PublicIngressError

_NEVER_RETRYABLE: tuple[type[PeerProtocolError], ...] = (
    AuthFailureError,
    ConfigMismatchError,
    ConventionMismatchError,
    ReportDisagreeError,
)


class FailureClass(StrEnum):
    """The PRD-05 connectivity failure classes."""

    RETRYABLE = "RETRYABLE"
    PACED = "PACED"
    BLOCKING = "BLOCKING"
    NON_RETRYABLE = "NON_RETRYABLE"


class RateLimitedError(PublicIngressError):
    """HTTP 429 from the provider: retryable, but only after pacing (`FR-061`)."""


def classify(failure: BaseException) -> FailureClass:
    """Return the PRD-05 class of *failure*.

    Order matters: the paced case is a `PublicIngressError` subclass and must be
    recognised before the general transport case, and integrity failures are
    checked before any retryable class so none can be reached by a later branch.
    """
    if isinstance(failure, RateLimitedError):
        return FailureClass.PACED
    if isinstance(failure, _NEVER_RETRYABLE):
        return FailureClass.NON_RETRYABLE
    if isinstance(failure, PublicIngressError):
        return FailureClass.RETRYABLE
    if isinstance(failure, PeerProtocolError):
        return FailureClass.BLOCKING
    return FailureClass.NON_RETRYABLE


def may_retry(failure: BaseException) -> bool:
    """Whether the retry scheduler may attempt *failure* again at all."""
    return classify(failure) in {FailureClass.RETRYABLE, FailureClass.PACED}
