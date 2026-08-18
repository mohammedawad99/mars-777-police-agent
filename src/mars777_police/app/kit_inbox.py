"""Where a pushed turn waits, and what it is allowed to wake.

The pinned wire is **symmetric push**: the opponent's turn arrives on our own
inbound server, on a FastMCP session, while the game loop is somewhere else
entirely. This is the seam between the two, and it exists so the loop can be
woken by exactly what it is owed.

**Only an authoritative newly accepted message wakes it.** A tolerated
duplicate proves the opponent is alive and discharges nothing, so it sets no
event - which is also what keeps the deadline honest: one clock per *expected*
message, so a stall burns the sender's budget and never ours. A loop that were
woken by every HTTP arrival could take two consecutive turns on stale state.

**Bounded by the window, and by nothing else.** The reorder window is the flood
rule; a second threshold beside it would be unreachable by construction. There
is no global instance and no singleton: one inbox belongs to one session's
sub-game, and a second one shares nothing with it.

No polling and no sleeping. `take` awaits an `asyncio.Event`, so a cancelled
wait leaves the state exactly as it found it.
"""

import asyncio
from dataclasses import dataclass, field

from .kit_delivery import DeliveryDecision, DeliveryState, decide
from .kit_messages import KitTurn
from .protocol_errors import StaleMessageError


@dataclass(slots=True)
class KitTurnInbox:
    """One sub-game's inbound turn stream, deduplicated and ordered."""

    window: int = 2
    expected: int = 1
    played: dict[int, str] = field(default_factory=dict)
    buffered: dict[int, KitTurn] = field(default_factory=dict)
    ready: list[KitTurn] = field(default_factory=list)
    equivocations: tuple[int, ...] = field(default=())
    arrived: asyncio.Event = field(default_factory=asyncio.Event)

    def offer(self, turn: KitTurn) -> tuple[KitTurn, ...]:
        """Apply what *turn* makes applicable, in step order, or refuse it."""
        decision = decide(self._state(), turn.step, turn.commit.value)
        if decision is DeliveryDecision.EQUIVOCATION:
            self.equivocations = (*self.equivocations, turn.step)
            raise StaleMessageError(
                f"step {turn.step} arrived under a second commit; the peer sealed two"
                " different turns for one step, which is equivocation, not a redelivery",
            )
        if decision is DeliveryDecision.VIOLATION:
            raise StaleMessageError(
                f"step {turn.step} is past the reorder window of {self.window} from"
                f" step {self.expected}; the window is the flood rule",
            )
        if decision in (DeliveryDecision.ABSORB, DeliveryDecision.DISCARD):
            return ()
        if decision is DeliveryDecision.BUFFER:
            self.buffered[turn.step] = turn
            return ()
        return self._apply(turn)

    def consume(self) -> tuple[KitTurn, ...]:
        """Take the applied turns nobody has read yet, and clear the wake-up."""
        taken, self.ready = tuple(self.ready), []
        self.arrived.clear()
        return taken

    async def take(self, timeout: float) -> tuple[KitTurn, ...]:
        """Wait for the message we are owed, bounded by the caller's deadline."""
        await asyncio.wait_for(self.arrived.wait(), timeout)
        return self.consume()

    def _state(self) -> DeliveryState:
        return DeliveryState(self.played, self.window, self.expected)

    def _apply(self, turn: KitTurn) -> tuple[KitTurn, ...]:
        """Accept *turn* and every buffered step it unblocks, in one order."""
        applied: list[KitTurn] = []
        current: KitTurn | None = turn
        while current is not None:
            self.played[current.step] = current.commit.value
            self.expected = current.step + 1
            applied.append(current)
            current = self.buffered.pop(self.expected, None)
        self.ready.extend(applied)
        self.arrived.set()
        return tuple(applied)
