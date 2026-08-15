"""What one sub-game's final audit is about, and what it concluded.

`LOG_CONTRACT.md` §"Stage 4E-R11-R1" classifies every log field exactly once.
Three of them - `entries[].verified`, `audit.result`, `audit.tampered_step` - are
**LOCAL-DERIVED-AUDIT**, "computed by the receiver, **never** accepted as peer
evidence". `AuditOutcome` is that local derivation, and it is deliberately a
value rather than a message: `FinalAuditVerdict` is local audit vocabulary and is
never transmitted.

`SubGameContext` carries the SHARED-AUDIT-INPUT identity the receiver must match
a disclosed document against - `game_id`, `game_uid`, `sub_game`, `config_sha256`
- so a document for another game or another locked config is refused before any
hashing happens.
"""

from dataclasses import dataclass
from enum import StrEnum

from .protocol_values import FinalAuditVerdict, Sha256Digest
from .sealed_record_values import ActorRole
from .turn_protocol_state import TurnEvidence


class AuditPhase(StrEnum):
    """The per-sub-game audit sequence, in the one order the timeline allows."""

    AWAITING_NONCES = "AWAITING_NONCES"
    AWAITING_DISCLOSURE = "AWAITING_DISCLOSURE"
    COMPLETE = "COMPLETE"


@dataclass(frozen=True, slots=True)
class SubGameContext:
    """The identity a disclosed audit document must match exactly."""

    game_id: str
    game_uid: str
    sub_game: int
    config_sha256: Sha256Digest
    peer_role: ActorRole
    peer_group_id: str

    def __post_init__(self) -> None:
        for name in ("game_id", "game_uid", "peer_group_id"):
            value = getattr(self, name)
            if type(value) is not str or not value:
                raise ValueError(f"{name} must be a non-empty str")
        if type(self.sub_game) is not int or self.sub_game < 1:
            raise ValueError("sub_game must be a positive int")


@dataclass(frozen=True, slots=True)
class AuditOutcome:
    """The receiver's own verdict, plus the first step that failed if any.

    `tampered_step` is derived here and never read from the document: a sender's
    claimed tampered step has no more standing than its claimed result.
    """

    verdict: FinalAuditVerdict
    tampered_step: int | None = None

    def __post_init__(self) -> None:
        if self.verdict is FinalAuditVerdict.VERIFIED_OK and self.tampered_step is not None:
            raise ValueError("a verified audit names no tampered step")
        if self.verdict is FinalAuditVerdict.TAMPERED and self.tampered_step is None:
            raise ValueError("a tampered audit must name the first failing step")

    @property
    def verified(self) -> bool:
        """Whether this sub-game may proceed to result agreement."""
        return self.verdict is FinalAuditVerdict.VERIFIED_OK


def require_aggregate(evidence: tuple[TurnEvidence, ...], sub_game: int) -> None:
    """Refuse an evidence aggregate that repeats a cursor or leaves its sub-game.

    A value rule, not an audit decision: it is the same check whether the
    aggregate is being built at construction or grown turn by turn, and both
    callers must apply it identically.
    """
    seen = [record.cursor for record in evidence]
    if len(set(seen)) != len(seen):
        raise ValueError("the evidence aggregate carries a duplicate cursor")
    if any(cursor.sub_game != sub_game for cursor in seen):
        raise ValueError("every evidence cursor must belong to this sub-game")
