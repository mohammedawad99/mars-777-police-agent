"""The group's one result-agreement authority, owned where the series is owned.

An alternating series is played by two backends and held by neither: each owns
three sub-games, and only the gateway ever sees all six. The result agreement is
a **series-wide** fact, so letting each backend keep its own half of it would
give one group two opinions about whether its result was agreed. This owns it
once, in the one place both backends already meet.

**It builds nothing early.** A `ResultExchange` needs the merged declaration,
all six settled rows and this group's own complete six-entry contribution. Until
every one of those exists there is no exchange, no core and no digest - and an
inbound request arriving before then is refused rather than answered from
incomplete state. That refusal is the honest answer: a series whose own half is
not assembled cannot agree anything.

**The peer's half is accepted only from the peer.** `ResultExchange` already
refuses a contribution whose `group_id` is not the authenticated sender's, and
`result_core_runtime` already refuses a commit that is not the one declared for
the role that sub-game was played in. Nothing here re-implements either.
"""

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field

from .peer_final_messages import ResultAgreement
from .protocol_errors import StaleMessageError
from .protocol_values import Sha256Digest
from .result_exchange import ResultExchange

Wait = Callable[[object], Awaitable[None]]
"""How this waits on a milestone the peer's inbound request will set."""

ExchangeBuilder = Callable[[], ResultExchange | None]
"""How the group assembles its exchange once every part exists, or `None`."""


@dataclass(slots=True)
class GroupResultAgreement:
    """One series' result agreement, assembled late and owned exactly once."""

    build: ExchangeBuilder
    exchange: ResultExchange | None = field(default=None)
    poll: float = field(default=0.5)
    """How often readiness is re-checked while waiting. Suspends, never spins."""

    def ready(self) -> ResultExchange | None:
        """The exchange, assembling it the first time every part is present."""
        if self.exchange is None:
            self.exchange = self.build()
        return self.exchange

    async def accept(
        self, agreement: ResultAgreement, sender_id: str, window: float
    ) -> Sha256Digest:
        """Answer the peer's single request with our own canonical digest.

        **A valid request may legitimately arrive before we are ready.** Both
        sides finish g06 at different moments, and the proposer sends the instant
        its own settlement completes - so the receiver can still be publishing
        its sixth contribution entry. That is a lifecycle race between two honest
        peers, not a fault in either, and refusing it would lose an agreement
        nobody got wrong.

        So this waits **boundedly** for its own half to assemble and then
        processes the *same* request. The wait is bounded by the counted
        watchdog the pairing already agreed, never open-ended, and it suspends
        rather than spins. If readiness never arrives the request is refused with
        an explicit not-ready error the sender may retry - no state is mutated
        and nothing is fabricated.

        **Malformed and unauthenticated requests never reach here**: the envelope
        is parsed and the sender authenticated before this is called, so neither
        is ever made to wait.

        **A repeat of a request already answered is idempotent.** The peer
        retries a transient transport failure by resending the same semantic
        value, and answering with the digest we already computed is the same
        answer - never a second pass over `ResultExchange`.
        """
        exchange = await self._ready_within(window)
        if exchange is None:
            raise StaleMessageError(
                "this group is not ready to agree a result yet: its own six contribution"
                " entries are not all present. The request is unprocessed and may be"
                " retried within the agreed window",
            )
        if exchange.peer_request_handled and exchange.local_digest is not None:
            return exchange.local_digest
        return exchange.accept_peer_request(agreement, sender_id)

    async def _ready_within(self, window: float) -> ResultExchange | None:
        """Our own half, waiting at most *window* seconds for it to assemble."""
        loop = asyncio.get_running_loop()
        deadline = loop.time() + max(window, 0.0)
        while True:
            exchange = self.ready()
            if exchange is not None:
                return exchange
            if loop.time() >= deadline:
                return None
            await asyncio.sleep(self.poll)

    async def settle(self, wait: "Wait") -> bool:
        """Run the two-request cadence from whichever side the existing rule names.

        The order is `ResultAgreementRuntime`'s, not ours: the byte-wise lower
        `group_id` proposes and then waits, and the other waits and then echoes
        the timestamp the proposer chose. Both directions must complete, because
        `is_agreed` needs both - a side that stopped at its own send would report
        a result the peer never answered.
        """
        exchange = self.ready()
        if exchange is None:
            return False
        if exchange.runtime.is_proposer:
            await exchange.open_agreement()
            await wait(exchange.milestones.requested)
            return exchange.is_agreed
        await wait(exchange.milestones.requested)
        adopted = exchange.timestamp
        if adopted is None:  # pragma: no cover - an accepted request always adopts one
            return False
        await exchange.send_response(adopted)
        return exchange.is_agreed

    @property
    def is_agreed(self) -> bool:
        """Whether both directions completed and both digests matched."""
        exchange = self.exchange
        return exchange is not None and exchange.is_agreed
