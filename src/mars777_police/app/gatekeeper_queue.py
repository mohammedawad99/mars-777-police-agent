"""Where a rate-limited provider call waits its turn, and what it does when full.

Guideline §5.3 asks for a queue rather than a refusal when the rate windows are
exhausted: FIFO order, a bounded depth from configuration, and backpressure only
at the boundary. This is that waiting room and nothing else - it holds no time,
no policy and no call.

**Order survives cancellation.** A caller that gives up leaves its place rather
than collapsing the queue behind it, so a caller that arrived later never
overtakes one that arrived earlier because somebody in the middle went away.
"""

from dataclasses import dataclass, field


class WaitingRoomFullError(Exception):
    """The queue is at its configured depth: backpressure, not a silent drop."""


@dataclass(slots=True)
class RateWindowQueue:
    """A bounded FIFO of tickets, served strictly in arrival order."""

    depth_limit: int
    _tickets: list[int] = field(default_factory=list)
    _issued: int = 0

    def __post_init__(self) -> None:
        if type(self.depth_limit) is not int or self.depth_limit <= 0:
            raise ValueError("queue depth must be a positive int")

    @property
    def depth(self) -> int:
        """How many callers are waiting right now."""
        return len(self._tickets)

    @property
    def head(self) -> int | None:
        """The ticket whose turn it is, or `None` when nobody is waiting."""
        return self._tickets[0] if self._tickets else None

    def join(self) -> int:
        """Take a place in the queue, or refuse when it is already full."""
        if len(self._tickets) >= self.depth_limit:
            raise WaitingRoomFullError(f"the waiting room holds {self.depth_limit} and is full")
        self._issued += 1
        ticket = self._issued
        self._tickets.append(ticket)
        return ticket

    def turn_of(self, ticket: int) -> bool:
        """Whether *ticket* is the one currently entitled to proceed."""
        return bool(self._tickets) and self._tickets[0] == ticket

    def serve(self, ticket: int) -> None:
        """Remove *ticket* after it has been let through."""
        self.leave(ticket)

    def leave(self, ticket: int) -> None:
        """Give up a place, keeping every remaining caller in arrival order."""
        if ticket in self._tickets:
            self._tickets.remove(ticket)
