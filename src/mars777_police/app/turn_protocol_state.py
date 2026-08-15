"""The live turn sequence as a typed phase, and the evidence the audit will need.

**Why a phase and not four booleans.** `commit_received`, `ack_sent`, `revealed`
and `consumed` admit sixteen combinations of which four are legal, and nothing
stops a caller reaching the other twelve. One `TurnPhase` admits exactly the
states the protocol has, so an out-of-order message is refused by construction
rather than by a conditional somebody has to remember to write.

**Two directions, never one slot.** The peer's commitment and our own are
different facts on different timelines - the peer commits and we acknowledge, we
commit and the peer acknowledges - so they are held separately. Merging them
would let one overwrite the other and make a stale message look current.

`TurnEvidence` is deliberately inert: it is what Stage 5-R2's audit needs to
associate a stored `h_commit` with the action and hint that were later revealed
for that cursor. It performs no verification and holds no secret - the `nonce`,
`state` and `intent` that would complete the sealed record are not disclosed
during live play and are not represented here.
"""

import asyncio
from dataclasses import dataclass, field
from enum import StrEnum

from ..domain.scent_emission import ScentEmission
from .protocol_values import Sha256Digest
from .sealed_record_values import ActorRole
from .turn_cursor import TurnCursor


@dataclass(slots=True)
class TurnMilestones:
    """The three inbound moments an autonomous driver has to wait for.

    A driver that polled would burn a core and still race; these let it suspend
    until the runtime has actually recorded the thing it needs. **They report
    state, they never hold it** - each is set only after the phase machine has
    already moved, so a waiter that wakes finds the transition complete rather
    than in progress. Nothing here decides whether a message was legal.

    One set per `TurnProtocolRuntime`, because a turn is the scope these facts
    live in: a global event would let one step's arrival wake another's waiter.
    """

    peer_committed: asyncio.Event = field(default_factory=asyncio.Event)
    acknowledged: asyncio.Event = field(default_factory=asyncio.Event)
    peer_revealed: asyncio.Event = field(default_factory=asyncio.Event)


class TurnPhase(StrEnum):
    """The peer-side turn sequence, in the one order the protocol allows."""

    AWAITING_COMMITMENT = "AWAITING_COMMITMENT"
    AWAITING_OUR_ACKNOWLEDGEMENT = "AWAITING_OUR_ACKNOWLEDGEMENT"
    AWAITING_REVEAL = "AWAITING_REVEAL"
    CONSUMED = "CONSUMED"


@dataclass(frozen=True, slots=True)
class PendingCommitment:
    """One commitment digest bound to the cursor it was sent for."""

    cursor: TurnCursor
    h_commit: Sha256Digest

    def matches(self, cursor: TurnCursor) -> bool:
        """Whether this commitment belongs to *cursor*."""
        return self.cursor == cursor


@dataclass(frozen=True, slots=True)
class AckEvidence:
    """One acknowledgement, as the official log records it.

    `LOG_CONTRACT.md` §C keeps the ack a separate event carrying the acked step,
    the acked digest and the acking role. The first two are copied from the
    commitment being acknowledged; `by_role` is **log attribution** - derived
    from the config-locked role mapping, never transmitted and never read from a
    peer message, exactly as Stage 4E-R3 froze it.
    """

    cursor: TurnCursor
    h_commit: Sha256Digest
    by_role: ActorRole


@dataclass(frozen=True, slots=True)
class TurnEvidence:
    """What a completed peer turn leaves behind for the Stage 5-R2 audit.

    The `h_commit` was received before the action was disclosed, so retaining
    both together is what later lets the audit - once the nonce and full log
    arrive - rebuild the sealed record and prove correspondence. Nothing here is
    verified now, and nothing here is secret.
    """

    cursor: TurnCursor
    h_commit: Sha256Digest
    action: object
    hint: str
    legal: bool
    scent: ScentEmission | None = None
    """What the peer said this turn deposited - an observation, not a verdict.

    Retained exactly as received and never recomputed here: the receiver cannot
    know where the sender stood, so live code holds the claim and the final audit
    re-renders it from the disclosed trajectory. Ours is never stored here."""
