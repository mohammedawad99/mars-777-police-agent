"""Immutable internal peer-protocol semantic message contracts.

The values application control flow consumes and produces, and that
``protocol.messages`` will later map to and from wire bytes - **never** wire JSON
itself (`MODULE_BOUNDARIES.md`, Stage 4E-R1/R2). No state is owned, nothing is
serialized, and nothing here computes a hash: a caller supplies an already
validated ``Sha256Digest``, so this module never learns what was hashed, how the
sealed record was canonicalized, or which nonce sealed it.

Of the ten peer-visible families in `PROTOCOL_TIMELINE.md`, exactly one is
implementable today (Stage 4E-R2): **Commitment**. The other nine remain blocked
on payload shapes, value representations and association shapes that no current
contract freezes - so no placeholder for them exists here.

Malformed construction raises the built-in ``ValueError``. That is the category
``FinalAuditVerdict`` already raises natively and that ``InvalidDigestError``
subclasses, so one ``except ValueError`` covers every value in the application
contract modules. No supporting error type is defined (Stage 4E-R2-FIX1).
"""

from dataclasses import dataclass

from ..domain.config_model import FIRST_SUB_GAME, FIXED_NUM_GAMES
from .protocol_values import Sha256Digest


@dataclass(frozen=True, slots=True)
class TurnCursor:
    """The transmitted identity of one turn-scoped message.

    Exactly ``(sub_game, step)`` (PRD-02 §8; PRD02-FR-044/FR-063). **No phase**:
    the receiver already owns the single authoritative ``ProtocolMachine`` and
    checks admissibility against it (FR-021/FR-062, STATE-003), so transmitting a
    phase would either duplicate that authority or be uncomputable in lockstep.

    A *projection*, never an owner: the sub-game index belongs to
    ``app.orchestrator`` and the step to ``domain.truth``. Validation here is
    **structural only**. ``sub_game`` may be bounded because ``num_games`` is
    globally FIXED at six, and the bound reads that one authority rather than
    restating it; ``step`` has no context-free ceiling, because ``max_moves`` is
    per-sub-game locked configuration this value deliberately does not carry.
    """

    sub_game: int
    step: int

    def __post_init__(self) -> None:
        _require_int(self.sub_game, "sub_game")
        _require_int(self.step, "step")
        if not FIRST_SUB_GAME <= self.sub_game <= FIXED_NUM_GAMES:
            raise ValueError(
                f"sub_game must be in [{FIRST_SUB_GAME}, {FIXED_NUM_GAMES}], got {self.sub_game}",
            )
        if self.step < 1:
            raise ValueError(f"step must be at least 1, got {self.step}")


@dataclass(frozen=True, slots=True)
class Commitment:
    """The peer-visible commitment: a turn cursor and the commitment digest.

    `PROTOCOL_TIMELINE.md` event 5 transmits "``H_commit`` **only**", and the
    cursor is required independently (PRD02-FR-044; PRD06-FR-086 rejects a second
    commitment for an already-committed ``(sub_game, step)``). Nothing else
    travels: the sealed record's state, move, intent, hint, role, sub-game and
    nonce stay inside the digest, and the hiding property of the commitment
    (PRD06-FR-067) is exactly why none of them may appear beside it.

    Composition **never coerces**. A raw 64-hex string is refused rather than
    wrapped, and a pair is refused rather than turned into a cursor, so each
    value keeps one authoritative constructor and a caller can always tell which
    contract validated a field.
    """

    cursor: TurnCursor
    h_commit: Sha256Digest

    def __post_init__(self) -> None:
        if type(self.cursor) is not TurnCursor:
            raise ValueError(
                f"cursor must be a TurnCursor, got {type(self.cursor).__name__}",
            )
        if type(self.h_commit) is not Sha256Digest:
            raise ValueError(
                f"h_commit must be a Sha256Digest, got {type(self.h_commit).__name__}",
            )


def _require_int(value: object, name: str) -> None:
    """Reject anything but a real ``int``; ``bool`` is an ``int`` and is refused.

    Accepting ``True`` as sub-game 1 would be exactly the silent coercion the
    project forbids, so the check is on the type itself, not ``isinstance``.
    """
    if type(value) is not int:
        raise ValueError(f"{name} must be an int, got {type(value).__name__}")
