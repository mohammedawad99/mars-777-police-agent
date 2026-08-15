"""Reaching agreement with the peer about a document, twice per series.

A config round and the final result are the same shape of problem: one side is
named by an existing deterministic rule, both sides have to speak, and neither
may act on the outcome until the other has. The sub-game loop is not the right
place to hold that - it is about turns - so the two cadences live here, next to
each other, where the symmetry is visible.

**They decide nothing.** Who opens a config round is `initial_proposer`'s call,
who proposes the result is `ResultAgreementRuntime.is_proposer`'s, what a lock
means is `ConfigLockRuntime`'s, and whether an agreement holds is
`ResultExchange.is_agreed`'s. These functions only order the sends and the waits.

**Every wait is on a milestone its own owner sets after mutating state**, so a
waiter that wakes finds the fact already true - the rule Stage 6C-B established
for one turn, applied to the two boundaries a turn never crosses.
"""

from collections.abc import Awaitable, Callable

from ..domain.negotiated_config import NegotiatedConfig
from .config_negotiation_runtime import initial_proposer
from .peer_runner import PeerRunner
from .pregame_session_runtime import PregameSessionRuntime
from .result_exchange import ResultExchange

Wait = Callable[["object"], Awaitable[None]]
"""Suspends until an `asyncio.Event` is set, bounded by the caller's deadline."""


async def agree_config(
    pregame: PregameSessionRuntime, runner: PeerRunner, config: NegotiatedConfig, wait: Wait
) -> None:
    """Exchange proposals for the open round, then exchange and verify locks.

    The byte-wise lower `group_id` opens, so the other side waits for that
    proposal before making its own - `propose` refuses to open out of turn. Both
    then wait until they have seen the peer's proposal before any lock travels,
    so the round is converged before either digest does.
    """
    if initial_proposer(config) != pregame.negotiation.group_id:
        await wait(pregame.milestones.proposal_seen)
    await runner.send_config_proposal(config)
    await wait(pregame.milestones.proposal_seen)
    await runner.send_config_lock()
    await wait(pregame.milestones.lock_verified)


async def agree_result(exchange: ResultExchange, runner: PeerRunner, wait: Wait) -> None:
    """Run the result cadence from whichever side the existing rule names.

    Both sides end up waiting for the peer's request, because `is_agreed` needs
    both directions: the proposer sends first and then waits, the non-proposer
    waits and then echoes the timestamp the proposer chose. A side that stopped
    at its own send would persist a result the peer had not answered.
    """
    if exchange.runtime.is_proposer:
        await runner.open_result_agreement()
        await wait(exchange.milestones.requested)
        return
    await wait(exchange.milestones.requested)
    timestamp = exchange.timestamp
    if timestamp is None:
        raise AssertionError("an accepted request carries the adopted timestamp")
    await runner.respond_to_result(timestamp)
