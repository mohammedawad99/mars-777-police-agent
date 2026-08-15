"""The inbound moments a series coordinator has to wait for, as values.

Stage 6C-B established the shape for one turn: an owner mutates its own state
and *then* signals, so a waiter that wakes always finds the transition finished.
The series needs the same thing twice more, at boundaries a single turn never
crosses - a config round the peer has to speak in first, and a result agreement
only one side may open.

**Values, not owners.** Each holds `asyncio.Event`s and decides nothing. The
facts stay where they already live: `PregameSessionRuntime` knows when a
proposal was accepted and when a lock verified, and `ResultExchange` knows when
the proposer's request arrived. These only make those moments awaitable.

**Scoped like the fact they report.** Pregame milestones are per round and are
therefore replaced when a round opens, exactly as `opening` and `seen` are; the
result milestone is series-final and is set once. `TurnMilestones` is
deliberately not reused - a turn is a different scope, and one event set for two
scopes would wake the wrong waiter.
"""

import asyncio
from dataclasses import dataclass, field


@dataclass(slots=True)
class PregameMilestones:
    """One config round's two inbound arrivals: a proposal, then a lock."""

    proposal_seen: asyncio.Event = field(default_factory=asyncio.Event)
    """The peer proposed for this round - so `opening` is settled and we may too."""

    lock_verified: asyncio.Event = field(default_factory=asyncio.Event)
    """The peer's lock evidence verified - so this round has something to record."""


@dataclass(slots=True)
class ResultMilestones:
    """The one inbound arrival the non-proposer of a series waits for."""

    requested: asyncio.Event = field(default_factory=asyncio.Event)
    """The proposer's agreement request arrived, carrying the timestamp to echo."""
