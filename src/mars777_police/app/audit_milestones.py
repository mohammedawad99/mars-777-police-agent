"""The one moment a sub-game's final audit becomes closable, as a value.

Closing a sub-game needs the peer's disclosure: `semantic_review` replays the
peer's own positions and refuses without them. Sending ours says nothing about
having received theirs, and two independent processes reach that point in
whichever order the network allows - so the side that arrives first has to
wait. This is what it waits on.

**A signal, not a second truth.** `AuditRuntime` keeps the nonce batch, the
disclosure, the verdict and the phase; this holds an `asyncio.Event` and knows
nothing. It is set last, after every one of those is installed, so a waiter
that wakes can read all of them immediately.

**One event covers both arrivals**, because the audit already orders them: a
disclosure is refused unless the phase is `AWAITING_DISCLOSURE`, and only the
accepted nonce batch moves it there. `COMPLETE` therefore implies an accepted
batch *and* an accepted disclosure, which is why no second event exists.
"""

import asyncio
from dataclasses import dataclass, field


@dataclass(slots=True)
class AuditMilestones:
    """One sub-game audit's single awaitable moment."""

    complete: asyncio.Event = field(default_factory=asyncio.Event)
    """The peer's disclosure was **accepted** and this audit is `COMPLETE`.

    Never set by a refusal: a disclosure that fails verification leaves the
    phase where it was, so the event still reports a fact rather than an
    attempt."""
