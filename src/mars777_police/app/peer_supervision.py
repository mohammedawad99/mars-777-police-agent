"""Where peer call deadlines and peer liveness are decided - in the application.

Two different clocks, deliberately kept apart.

**The per-call response timeout** bounds one request. After `CONFIG_LOCKED` it is
`network_and_league.response_timeout_sec` from the locked `NegotiatedConfig` -
never a constant, because 30 is that member's Appendix-F *baseline* and the peers
may agree otherwise. Before a config exists there is nothing to read, so the
bound is the **negotiation window** the state already owns (`PRD02-FR-022`,
`CONFIG_CONTRACT.md` §R12-FIX-I); it is injected rather than named here, so this
module introduces no second numeric requirement.

**The watchdog** bounds peer *progress*, not one call, and it is an application
concern: transport must never decide a sanction. On expiry this surfaces the
existing `E-TIMEOUT-WATCHDOG` identity and stops - escalation and technical loss
belong to the game layer.
"""

from collections.abc import Callable
from dataclasses import dataclass

from ..domain.negotiated_config import NegotiatedConfig
from .protocol_errors import LocalDefectError

WATCHDOG_TIMEOUT = "E-TIMEOUT-WATCHDOG"
"""The existing `ERROR_MODEL.md` identity. No error id was created."""


class WatchdogTimeoutError(Exception):
    """Peer progress stalled past the locked threshold.

    Deliberately **not** a `PeerProtocolError`: it crosses no wire and accuses
    the peer of no protocol fault. It is a local supervision signal, and the
    layer that owns sanction decides what it means.
    """

    error_id = WATCHDOG_TIMEOUT


@dataclass(frozen=True, slots=True)
class TimeoutPolicy:
    """Derives each call's deadline from the state the project already holds."""

    bootstrap_seconds: float

    def __post_init__(self) -> None:
        if self.bootstrap_seconds <= 0:
            raise LocalDefectError("the negotiation window must be positive")

    def bootstrap(self) -> float:
        """The pre-lock bound: the injected negotiation window."""
        return self.bootstrap_seconds

    def for_config(self, config: NegotiatedConfig) -> float:
        """The post-lock bound: the negotiated `response_timeout_sec`."""
        return float(config.network_and_league.response_timeout_sec)


@dataclass(frozen=True, slots=True)
class Watchdog:
    """Supervises peer liveness against the locked `watchdog_timeout_sec`.

    The clock is injected, so a test proves the threshold without waiting for
    it. `progress` records that the peer did something qualifying; `check`
    raises once the gap since that moment exceeds the limit.
    """

    limit_seconds: float
    now: Callable[[], float]

    @classmethod
    def for_config(cls, config: NegotiatedConfig, now: Callable[[], float]) -> "Watchdog":
        """Build the watchdog from the locked config's own threshold."""
        return cls(float(config.network_and_league.watchdog_timeout_sec), now)

    def check(self, last_progress: float) -> None:
        """Raise the existing identity when the peer has stalled too long."""
        if self.now() - last_progress > self.limit_seconds:
            raise WatchdogTimeoutError(WATCHDOG_TIMEOUT)

    def is_expired(self, last_progress: float) -> bool:
        """Report the same fact without raising, for a supervisor loop."""
        return self.now() - last_progress > self.limit_seconds
