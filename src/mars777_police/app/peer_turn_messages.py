"""The per-turn peer-visible semantic message families.

The three families `PROTOCOL_TIMELINE.md` events 5, 6 and 7 put on the wire.
Moved here from `app.peer_messages` at Stage 4E-R7 **unchanged**: that module had
reached its line budget holding every value, so ownership was split while
`app.peer_messages` stayed the public façade. No state is owned, nothing is
serialized and nothing computes a hash - callers supply already-validated
values. Malformed construction raises the built-in ``ValueError``, the category
`FinalAuditVerdict` raises natively and `InvalidDigestError` subclasses, so one
``except ValueError`` covers every application contract value and no supporting
error type is defined.
"""

from dataclasses import dataclass

from ..domain.actions import BarrierAction, MoveAction, PhysicalAction
from ..domain.scent_emission import ScentEmission
from .capture_values import CaptureClaim
from .protocol_values import Sha256Digest
from .turn_cursor import TurnCursor


@dataclass(frozen=True, slots=True)
class Commitment:
    """The peer-visible commitment: a turn cursor and the commitment digest.

    `PROTOCOL_TIMELINE.md` event 5 transmits "``H_commit`` **only**", with the
    cursor required independently (PRD02-FR-044; PRD06-FR-086). Nothing else
    travels: the sealed record's state, move, intent, hint, role, sub-game and
    nonce stay inside the digest, and the hiding property (PRD06-FR-067) is
    exactly why none may appear beside it. Composition **never coerces** - a raw
    64-hex string is refused rather than wrapped, and a pair is refused rather
    than turned into a cursor - so each value keeps one authoritative constructor.
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


@dataclass(frozen=True, slots=True)
class Acknowledgement:
    """The peer-visible acknowledgement: the turn cursor and the acked digest.

    Ch 5 §5.3.2 and PRD06-FR-082 make it binding receipt of a **specific**
    ``H_commit`` for a **specific** ``(sub_game, step)`` - exactly these two
    members. Three deliberate absences (Stage 4E-R3): ``by_role`` is **log
    attribution** the writer derives from send/receive direction and the
    ``CONFIG_LOCKED`` role map, so nothing is transmitted for a hostile peer to
    forge; ``ack_of_step`` is the *persisted* name of ``cursor.step``; and there
    is no ``accepted`` flag, because an acknowledgement
    is positive by existing while a stale one is a live rejection. It shares its
    component types with `Commitment` and is still a different family, carried by
    the class identity, so no message-kind value exists.
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


@dataclass(frozen=True, slots=True)
class Reveal:
    """The peer-visible reveal: the turn cursor, the chosen action and the hint.

    Ch 5 §5.3.2 (p.51) sends *"the action (Move) and the verbal sentence"* with
    the nonce hidden until final audit, so ordinary reveal is deliberately
    incomplete beside audit material: no nonce, state, intent, role, sealed record
    or ``H_commit``. The member is ``action`` because it holds the domain's
    `PhysicalAction`; the *sealed* key stays ``move``, mapped later by the
    canonical layer. That alias is a union, so the rule is exact membership
    of ``(MoveAction, BarrierAction)`` - never ``type(x) is PhysicalAction`` - and
    composition **never coerces**: a bare ``Move``, a ``Position``, a token or a
    canonical mapping is refused rather than wrapped, because building an action
    is the domain's job and raises its own ``DomainError``, while a wrong
    component *here* is a message fault raising ``ValueError``. ``hint`` is a
    ``str`` structurally - ``hint_max_words`` is locked config and stays LIVE.
    """

    cursor: TurnCursor
    action: PhysicalAction
    hint: str
    capture_claim: CaptureClaim | None = None
    """The police's optional same-cell declaration; never sealed, never a nonce."""

    scent_emission: ScentEmission | None = None
    """What this action deposited, for the peer to observe (`..._SCENT_V2`).

    Structurally optional so a V1 reveal still constructs and still parses; the
    negotiated posture, not this value, decides whether absence is legal. It
    carries no centre, no source cell and no role - only the deposits the locked
    model produces - and it is **not** sealed: the commitment stays eight
    members, and the final audit re-renders the emission from the disclosed
    trajectory rather than trusting this copy."""

    def __post_init__(self) -> None:
        if type(self.cursor) is not TurnCursor:
            raise ValueError(f"cursor must be a TurnCursor, got {type(self.cursor).__name__}")
        if type(self.action) not in (MoveAction, BarrierAction):
            raise ValueError(
                f"action must be a MoveAction or BarrierAction, got {type(self.action).__name__}",
            )
        if type(self.hint) is not str:
            raise ValueError(f"hint must be a str, got {type(self.hint).__name__}")
        if self.capture_claim is not None and type(self.capture_claim) is not CaptureClaim:
            raise ValueError(
                f"capture_claim must be a CaptureClaim, got {type(self.capture_claim).__name__}",
            )
        if self.scent_emission is not None and type(self.scent_emission) is not ScentEmission:
            raise ValueError(
                f"scent_emission must be a ScentEmission, got {type(self.scent_emission).__name__}",
            )
