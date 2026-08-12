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

from dataclasses import dataclass
from enum import StrEnum

from .protocol_values import Sha256Digest
from .sealed_record_values import ActorRole
from .turn_cursor import TurnCursor


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
