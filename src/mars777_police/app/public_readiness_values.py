"""The local, machine-readable vocabulary of public-network readiness.

**These are not peer errors.** `E-NET-NOT-PUBLIC`, `E-NET-STALE-ENDPOINT` and
`E-NET-CONVENTION-UNSET` are named by `PRD05-FR-004`, `FR-013` and `FR-032` as
*reasons a local gate refuses counted play*. They never cross `ToolError`, they
are not `PeerProtocolError` subclasses, and they leave the peer error inventory
at its frozen size - a refusal to start is not an accusation against the peer.

The ten checks are `PRD05-FR-021` (a)-(j) exactly, in the order the requirement
states them. There is no eleventh member and none may be added: the gate's value
is that it is the *published* list, not a superset someone found useful.
"""

from dataclasses import dataclass
from enum import StrEnum


class PublicReadinessReason(StrEnum):
    """The exact PRD-05 local refusal reasons. Local only, never peer-facing."""

    NOT_PUBLIC = "E-NET-NOT-PUBLIC"
    STALE_ENDPOINT = "E-NET-STALE-ENDPOINT"
    CONVENTION_UNSET = "E-NET-CONVENTION-UNSET"


class ReadinessCheck(StrEnum):
    """`PRD05-FR-021` (a)-(j), in requirement order."""

    LOCAL_SERVER_BOUND = "a"
    PUBLIC_TUNNEL_ESTABLISHED = "b"
    OWN_PUBLIC_URL_NON_LOOPBACK = "c"
    OPPONENT_ENDPOINT_KNOWN = "d"
    OUTBOUND_REACHABILITY = "e"
    INBOUND_REACHABILITY = "f"
    EXPECTED_PEER_IDENTITY = "g"
    STEP0_AUTHENTICATED = "h"
    CONFIG_UNMUTATED_SINCE_LOCK = "i"
    PROFILE_AND_CONVENTION_FROZEN = "j"


CHECK_ORDER: tuple[ReadinessCheck, ...] = tuple(ReadinessCheck)


@dataclass(frozen=True, slots=True)
class CheckOutcome:
    """One check's verdict, with a reason **only** where the PRD names one."""

    check: ReadinessCheck
    passed: bool
    reason: PublicReadinessReason | None = None

    def __post_init__(self) -> None:
        if type(self.passed) is not bool:
            raise ValueError("passed must be a bool")
        if self.passed and self.reason is not None:
            raise ValueError("a passing check carries no refusal reason")


@dataclass(frozen=True, slots=True)
class PublicReadinessVerdict:
    """The machine-readable verdict `PRD05-FR-023` requires.

    `is_ready` is conjunctive by construction: it is true only when all ten
    checks are present and all ten passed, so a verdict built from a partial
    list can never read as ready.
    """

    outcomes: tuple[CheckOutcome, ...]

    def __post_init__(self) -> None:
        seen = tuple(outcome.check for outcome in self.outcomes)
        if seen != CHECK_ORDER:
            raise ValueError("a verdict must carry the ten FR-021 checks in order")

    @property
    def is_ready(self) -> bool:
        """True only when every one of the ten checks passed."""
        return all(outcome.passed for outcome in self.outcomes)

    @property
    def failures(self) -> tuple[CheckOutcome, ...]:
        """Every failed check, in requirement order."""
        return tuple(outcome for outcome in self.outcomes if not outcome.passed)

    @property
    def reasons(self) -> tuple[PublicReadinessReason, ...]:
        """The distinct PRD reason codes present, in first-seen order."""
        found: list[PublicReadinessReason] = []
        for outcome in self.outcomes:
            if outcome.reason is not None and outcome.reason not in found:
                found.append(outcome.reason)
        return tuple(found)
