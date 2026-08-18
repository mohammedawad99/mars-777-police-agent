"""Our sealed chain for one KIT sub-game, and the reveal that discloses it.

The pinned wire seals one record per half-turn - `{payload, nonce, commit}` -
and discloses the whole chain at the end, for the **opponent** to re-hash with
its own serializer. Which is why nothing here computes a digest of its own: the
codec the series froze does that, and the nonce comes from the port that owns
freshness.

**The nonce is why the phases exist.** A chain that accepted a new turn after the
opponent already held our nonces would be a turn we could have chosen knowing
what they hold, so sealing ends when the reveal is taken.

Our payload is deliberately *richer* than the kit minimum - it carries the step,
sub-game, role, move, intent, hint, position and declared barriers - because we
already hold that evidence and disclosing it at seal time costs nothing the final
audit would not reveal anyway. It is our schema offered, never a shape we require
back: the kit is explicit that payload key sets need not match across teams.
"""

from dataclasses import dataclass, field

from ..domain.actions import PhysicalAction
from ..domain.board import Position
from ..protocol.commitment_codec import commitment_for
from .commitment_codecs import CommitmentCodec
from .kit_messages import KitAuditReveal, KitRecord, KitResultClaim, KitRole
from .kit_payload import PeerPayload, kit_payload
from .nonce_source import NonceSourcePort
from .protocol_errors import StaleMessageError
from .protocol_values import Sha256Digest
from .sealed_record_values import ActorRole, Intent
from .turn_cursor import TurnCursor


@dataclass(slots=True)
class KitRecordChain:
    """One sub-game's sealed records, in the order they were sealed."""

    codec: CommitmentCodec
    nonces: NonceSourcePort
    records: tuple[KitRecord, ...] = field(default=())
    disclosed: bool = field(default=False)

    def seal(
        self,
        *,
        cursor: TurnCursor,
        role: ActorRole,
        action: PhysicalAction,
        intent: Intent,
        hint: str,
        own_position: Position,
        barriers: tuple[Position, ...],
    ) -> KitRecord:
        """Seal one half-turn and keep it. The digest is the frozen codec's."""
        if self.disclosed:
            raise StaleMessageError(
                "this chain has already been disclosed; a turn sealed after the"
                " opponent holds our nonces is a turn we could have chosen knowing them",
            )
        payload = kit_payload(
            cursor=cursor,
            role=role,
            action=action,
            intent=intent,
            hint=hint,
            own_position=own_position,
            barriers=barriers,
        )
        nonce = self.nonces.fresh()
        record = KitRecord(
            PeerPayload(payload),
            nonce.value,
            Sha256Digest(commitment_for(self.codec, payload, nonce.value)),
        )
        self.records = (*self.records, record)
        return record

    def reveal(self, sender: KitRole, claim: KitResultClaim) -> KitAuditReveal:
        """Disclose the whole chain with its nonces, once, and seal no more."""
        self.disclosed = True
        return KitAuditReveal(sender, self.records, claim)
