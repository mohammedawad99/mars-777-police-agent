"""How long a starting process may keep looking for a peer that is not up yet.

Two independent processes start in whatever order an operator runs them, so the
first one up finds nothing to dial. That is **lifecycle**, not protocol: nothing
has been agreed, no commitment exists, and no request needs replaying - the only
thing to redo is opening the session.

**The numbers are supplied, never named.** `AutonomousBoot` reads the bound off
the locked config's own `watchdog_timeout_sec` through the existing
`TimeoutPolicy`, so this module introduces no second timeout contract. The pause
is implementation timing - it decides nothing a peer can observe - and it is
deterministic on purpose: a random one would make a failed startup
irreproducible.

**The retryable set is one type, and it is narrow by construction.**
`PeerClient` translates a refused connection into the existing local
`E-TRANSPORT` category before anything else sees it. Every `PeerProtocolError` -
auth, config, stale, malformed - is an *answer* from a peer that is already
there, and retrying an answer would turn a refusal into a hang.
"""

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from .app.protocol_errors import LocalDefectError
from .transport.wire_errors import TransportFailureError


@dataclass(frozen=True, slots=True)
class StartupBudget:
    """The bound and the cadence of one process's search for its opponent."""

    total_seconds: float
    pause_seconds: float

    def __post_init__(self) -> None:
        for name in ("total_seconds", "pause_seconds"):
            if getattr(self, name) <= 0:
                raise LocalDefectError(f"{name} must be positive")

    def retryable(self, failure: BaseException) -> bool:
        """True only for a peer that is not listening **yet**."""
        return isinstance(failure, TransportFailureError)

    async def keep_trying(self, establish: Callable[[], Awaitable[None]]) -> None:
        """Call *establish* until it succeeds, the budget ends, or it is refused.

        The last failure escapes with its own identity rather than a summary, so
        a caller that gives up learns *why* the peer never arrived.
        """
        loop = asyncio.get_running_loop()
        deadline = loop.time() + self.total_seconds
        while True:
            try:
                await establish()
                return
            except BaseException as failure:
                if not self.retryable(failure) or loop.time() >= deadline:
                    raise
                await asyncio.sleep(self.pause_seconds)
