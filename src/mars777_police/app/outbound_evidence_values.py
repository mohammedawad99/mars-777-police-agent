"""What we keep about our own sealed turns, and what we let anyone else see.

Two values with deliberately opposite exposure. `SealedTurnRecord` is the whole
truth about one turn we committed - including the three members that stay secret
until the final audit - and it never leaves this package's producer.
`PreparedTurn` is what the runner is allowed to send: a `Commitment` now and a
`Reveal` later, both already frozen elsewhere as peer-visible families.

Keeping them apart is the point. If preparation returned the sealed record, a
caller could reveal a nonce early by accident, and the commit-reveal scheme only
works because the nonce is unavailable until everyone has committed.
"""

from dataclasses import dataclass
from enum import StrEnum

from ..domain.actions import PhysicalAction
from .peer_turn_messages import Commitment, Reveal
from .protocol_values import NonceValue, Sha256Digest
from .sealed_record_values import ActorRole, Intent, SealedState
from .turn_cursor import TurnCursor


class EvidencePhase(StrEnum):
    """The producer's one-way lifecycle for a single sub-game."""

    OPEN = "OPEN"
    NONCES_DISCLOSED = "NONCES_DISCLOSED"
    COMPLETE = "COMPLETE"


@dataclass(frozen=True, slots=True)
class LocalEvidenceContext:
    """The identity every disclosed entry of this sub-game is bound to.

    Ours, not the peer's: these are the values we already hold locally, so the
    disclosure writer never has to accept one back from a caller.
    """

    game_id: str
    game_uid: str
    sub_game: int
    config_sha256: Sha256Digest
    role: ActorRole

    def __post_init__(self) -> None:
        for name in ("game_id", "game_uid"):
            if not getattr(self, name):
                raise ValueError(f"{name} must be non-empty")
        if type(self.sub_game) is not int or self.sub_game < 1:
            raise ValueError(f"sub_game must be a positive int, got {self.sub_game!r}")


@dataclass(frozen=True, slots=True)
class SealedTurnRecord:
    """Everything we sealed for one turn, including what stays secret.

    Frozen and built from already-valid semantic values, so the disclosure the
    audit needs is rendered from this rather than reassembled from memory of
    what was sent.
    """

    cursor: TurnCursor
    state: SealedState
    action: PhysicalAction
    intent: Intent
    hint: str
    nonce: NonceValue
    commit: Sha256Digest


@dataclass(frozen=True, slots=True)
class PreparedTurn:
    """The two peer-visible values one prepared turn yields.

    Deliberately carries no nonce, no sealed state and no intent: a runner
    holding this cannot leak them, whatever it does with the value.
    """

    commitment: Commitment
    reveal: Reveal
