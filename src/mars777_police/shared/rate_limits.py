"""What a local provider rate-limit policy is, and which versions we can run.

The excellence guideline §5.2 requires every rate limit to be read from a
configuration file and never hardcoded, and §8.1 requires that file to carry an
explicit version starting at `1.00`. This module is the value side of both: the
shape a policy has, the values it refuses, and the versions this build supports.

**These are local operational limits for provider calls.** They are emphatically
**not** the peer-negotiated `RateLimiterTerms`: those are Appendix-F floors
agreed with an opponent, carried inside the signed configuration core and
covered by `config_sha256`. Nothing here crosses the wire, enters Step-0, or
reaches an artifact - conflating the two would make a local operational choice
look like a term the opponent agreed to.

**The version is text.** `1.00` written as a JSON number would be read back as
`1.0`, which is a second truth about the same value; stored as a string it round
trips exactly, the way `shared/version.py` handles the same problem for the
software version.
"""

from dataclasses import dataclass
from typing import Final

SUPPORTED_RATE_LIMIT_VERSIONS: Final[frozenset[str]] = frozenset({"1.00"})
"""Every rate-limit configuration revision this build can run."""


class RateLimitConfigError(Exception):
    """A local rate-limit configuration this build cannot act on.

    Always local: no peer can cause it and none is told about it.
    """


def _positive(value: object, name: str) -> int:
    if type(value) is not int or value <= 0:
        raise RateLimitConfigError(f"{name} must be a positive int, got {value!r}")
    return value


def _not_negative(value: object, name: str) -> int:
    if type(value) is not int or value < 0:
        raise RateLimitConfigError(f"{name} must be a non-negative int, got {value!r}")
    return value


@dataclass(frozen=True, slots=True)
class RateLimitPolicy:
    """The complete control policy for one provider operation."""

    requests_per_minute: int
    requests_per_hour: int
    concurrent_max: int
    queue_depth: int
    max_retries: int
    retry_after_seconds: int
    max_backoff_seconds: int
    retryable_statuses: tuple[int, ...]

    def __post_init__(self) -> None:
        for name in ("requests_per_minute", "requests_per_hour", "concurrent_max", "queue_depth"):
            _positive(getattr(self, name), name)
        for name in ("max_retries", "retry_after_seconds", "max_backoff_seconds"):
            _not_negative(getattr(self, name), name)
        if self.max_backoff_seconds < self.retry_after_seconds:
            raise RateLimitConfigError(
                "max_backoff_seconds must not be below retry_after_seconds",
            )
        if type(self.retryable_statuses) is not tuple:
            raise RateLimitConfigError("retryable_statuses must be a tuple")
        for status in self.retryable_statuses:
            if type(status) is not int or not 100 <= status <= 599:
                raise RateLimitConfigError(f"retryable_statuses holds {status!r}")


@dataclass(frozen=True, slots=True)
class RateLimitConfig:
    """One versioned file: a default policy and any per-operation overrides."""

    version: str
    default: RateLimitPolicy
    operations: dict[str, RateLimitPolicy]

    def __post_init__(self) -> None:
        if self.version not in SUPPORTED_RATE_LIMIT_VERSIONS:
            supported = ", ".join(sorted(SUPPORTED_RATE_LIMIT_VERSIONS))
            raise RateLimitConfigError(
                f"rate_limits.version {self.version!r} is not supported by this build;"
                f" supported: {supported}",
            )

    def policy_for(self, operation: str) -> RateLimitPolicy:
        """Return the policy governing *operation*, or the default."""
        return self.operations.get(operation, self.default)
