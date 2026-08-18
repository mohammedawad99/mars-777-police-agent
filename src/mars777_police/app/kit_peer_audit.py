"""Gate 1 over a KIT peer's disclosed chain: do its bytes reproduce its digests?

**Cryptographic correspondence and nothing else.** A faithfully sealed illegal
move passes this, which is exactly why the semantic gate is a separate question
with four answers rather than two - and why a fact the peer's schema simply does
not carry is `NOT_CHECKABLE` rather than an accusation of tampering.

The pinned kit standardises this correspondence and explicitly **not** payload
meaning: peers need not seal the same keys, and each side re-hashes what the
other revealed with its own serializer. So a peer's chain can verify perfectly
while telling us very little about whether it played legally, and reporting the
two as one number would be the whole failure this split exists to avoid.
"""

from .audit_status import CheckStatus
from .commitment_codecs import CommitmentCodec
from .kit_audit import ExternalTurn, crypto_gate
from .kit_messages import KitAuditReveal
from .sealed_record_values import ActorRole
from .turn_cursor import TurnCursor


def peer_chain_verified(reveal: KitAuditReveal, sub_game: int, codec: CommitmentCodec) -> bool:
    """Whether every record the peer disclosed reproduces the digest it sealed."""
    return all(
        crypto_gate(
            ExternalTurn(
                TurnCursor(sub_game, index),
                ActorRole(reveal.sender.value),
                record.payload,
                record.nonce,
                record.commit.value,
            ),
            codec,
        )
        is CheckStatus.VERIFIED
        for index, record in enumerate(reveal.records, start=1)
    )
