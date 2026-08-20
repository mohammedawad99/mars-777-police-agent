"""What the gate records about a provider call, and what it deliberately omits.

Guideline §5.1 asks for every external call to be logged for monitoring. What is
useful is the shape of the call - which operation, whether it waited, how many
attempts it took, how it ended - and what is dangerous is the content. So no
request body, no header, no credential and no provider payload is recorded here;
a diagnostic that leaks key material is worse than no diagnostic at all.
"""

from dataclasses import dataclass
from enum import StrEnum


class CallOutcome(StrEnum):
    """How one gated provider call ended."""

    SUCCEEDED = "SUCCEEDED"
    """The operation ran and returned."""

    FAILED = "FAILED"
    """The operation ran and raised, with no attempts left or none allowed."""

    REJECTED = "REJECTED"
    """Backpressure: the waiting room was full, so the call never ran."""

    REFUSED = "REFUSED"
    """The concurrency ceiling was already reached, so the call never ran."""


@dataclass(frozen=True, slots=True)
class GatekeeperCall:
    """One observation, safe to print anywhere."""

    operation: str
    outcome: CallOutcome
    attempts: int
    queued: bool
    throttled: bool
    elapsed_seconds: float
