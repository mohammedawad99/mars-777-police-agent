"""The `CommitmentPort` adapter: the audit consumer's legal route to the digest.

`app` may not import `protocol`, so the final-audit runtime cannot call
`compute_commitment` directly. This adapter closes that edge the way every other
R16 port does - the application depends on a `Protocol` in `app.ports`, and this
concrete class satisfies it structurally from the outer side.

It adds **no** cryptography. `recompute` is `compute_commitment` and `matches` is
`commitment_matches`, so the live producer and the audit verifier hash the same
bytes through the same code. A second implementation would be a second thing to
drift, and a drifting verifier reports tampering that never happened.
"""

from dataclasses import dataclass

from ..app.protocol_values import NonceValue, Sha256Digest
from ..app.sealed_record_values import ActorRole, Intent, SealedState
from ..app.turn_cursor import TurnCursor
from ..domain.actions import PhysicalAction
from .commitment import commitment_matches, compute_commitment


@dataclass(frozen=True, slots=True)
class CommitmentRecomputer:
    """The `CommitmentPort` adapter over this module's frozen primitives.

    It adds no cryptography: `recompute` is `compute_commitment` and `matches` is
    `commitment_matches`, so the audit consumer and the live producer hash the
    same bytes through the same code. A second implementation would be a second
    thing to drift, and a drifting verifier reports tampering that never happened.
    """

    def recompute(
        self,
        *,
        state: SealedState,
        action: PhysicalAction,
        intent: Intent,
        hint: str,
        cursor: TurnCursor,
        role: ActorRole,
        nonce: NonceValue,
    ) -> Sha256Digest:
        """Return `H_commit` over the eight-member sealed record."""
        return compute_commitment(
            state=state,
            action=action,
            intent=intent,
            hint=hint,
            cursor=cursor,
            role=role,
            nonce=nonce,
        )

    def matches(self, expected: Sha256Digest, recomputed: Sha256Digest) -> bool:
        """Whether two digests are equal."""
        return commitment_matches(expected, recomputed)
