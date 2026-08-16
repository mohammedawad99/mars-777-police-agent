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


@dataclass(slots=True)
class PeerDeadline:
    """The one outbound deadline, from the bootstrap window to the locked one.

    The negotiated `response_timeout_sec` never reached a request: the client
    was built once with a constant and nothing rebound it, so the value both
    peers agreed governed nothing. `for_locked_config` and `for_config` were
    correct and unused, which is exactly why unit tests could not see it.

    The authority is read rather than pushed. *locked* answers with the config
    only once a lock has been **verified**, so an adopted candidate, a peer's
    proposal or a refused lock all leave the deadline where it was, and no
    caller has to remember to rebind at the right moment.

    It latches: once a lock has been seen the agreed deadline is kept for the
    rest of the series, so opening the next sub-game's round never drops a
    running series back onto the pre-lock window.

    Without a *locked* source it stays on the negotiation window for good,
    which is what a client that never takes part in a lock should do.
    """

    policy: TimeoutPolicy
    locked: Callable[[], NegotiatedConfig | None] = lambda: None
    held: float | None = None

    def seconds(self) -> float:
        """The deadline a request should use right now."""
        config = self.locked()
        if config is not None:
            self.held = self.policy.for_config(config)
        return self.policy.bootstrap() if self.held is None else self.held


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
