"""How a live window hears about a turn without ever being able to affect one.

`PRD07-FR-008` is explicit: GUI failure, slowness or disconnection must not stop
or alter the game, and the channel is **lossy by design**. So this is a one-way
drop box, not a queue: the runtime leaves the newest snapshot and walks away,
a reader takes whatever is there, and nothing about either operation can block,
grow without bound, or raise into the game.

**A sink that misbehaves is the sink's problem.** `publish` swallows whatever a
viewer raises, because a window that crashed must not be able to end a match
that was going fine.
"""

from dataclasses import dataclass, field
from typing import Protocol

from .live_view_values import LiveViewSnapshot


class LiveViewSink(Protocol):
    """Somewhere a snapshot can be left. Never asked for anything back."""

    def publish(self, snapshot: LiveViewSnapshot) -> None:
        """Take *snapshot*, or fail privately. Never raise into the caller."""
        ...


@dataclass(slots=True)
class LatestSnapshot:
    """The newest snapshot and nothing older: one slot, latest wins.

    Bounded by construction rather than by a policy that could be tuned wrong.
    A viewer that reads slowly misses intermediate turns, which is exactly what
    "lossy by design" means and is preferable to a queue that could grow while
    a turn is being played.
    """

    current: LiveViewSnapshot | None = field(default=None)
    published: int = field(default=0)
    dropped: int = field(default=0)

    def publish(self, snapshot: LiveViewSnapshot) -> None:
        """Replace whatever was there. Constant time, never blocking."""
        if self.current is not None:
            self.dropped += 1
        self.current = snapshot
        self.published += 1

    def take(self) -> LiveViewSnapshot | None:
        """The newest snapshot, leaving it in place for the next reader."""
        return self.current


@dataclass(slots=True)
class GuardedSink:
    """A sink whose failures stay inside it.

    Wraps any viewer so that a rendering fault, a closed window or a slow
    consumer that raises cannot reach the runtime that published.
    """

    inner: LiveViewSink
    failures: int = field(default=0)

    def publish(self, snapshot: LiveViewSnapshot) -> None:
        """Offer the snapshot; record, but never re-raise, whatever went wrong."""
        try:
            self.inner.publish(snapshot)
        except Exception:  # a viewer must never end a match
            self.failures += 1


class NoViewer:
    """The default: nobody is watching, and publishing costs one call."""

    def publish(self, snapshot: LiveViewSnapshot) -> None:
        """Discard the snapshot. There is no window to tell."""


NO_VIEWER: LiveViewSink = NoViewer()
"""Shared because it is stateless; composition uses it unless a viewer attaches."""
