"""Immutable internal peer-protocol semantic message contracts.

The values application control flow consumes and produces, and that
``protocol.messages`` will later map to and from wire bytes - **never** wire JSON
itself (`MODULE_BOUNDARIES.md`). No state is owned, nothing is serialized and
nothing computes a hash - callers supply already-validated values.

Three of the ten peer-visible families in `PROTOCOL_TIMELINE.md` are
implementable - **Commitment**, **Acknowledgement** and **Reveal**; the other
seven stay blocked on payload, value and association shapes no current contract
freezes, so no placeholder exists here. Malformed construction raises the
built-in ``ValueError`` - the category ``FinalAuditVerdict`` raises natively and
``InvalidDigestError`` subclasses - so one ``except ValueError`` covers every
application contract value, and no supporting error type is defined.
"""

from dataclasses import dataclass

from ..domain.actions import BarrierAction, MoveAction, PhysicalAction
from ..domain.config_model import FIRST_SUB_GAME, FIXED_NUM_GAMES
from .protocol_values import Sha256Digest


@dataclass(frozen=True, slots=True)
class TurnCursor:
    """The transmitted identity of one turn-scoped message.

    Exactly ``(sub_game, step)`` (PRD-02 §8; PRD02-FR-044/FR-063). **No phase**:
    the receiver owns the single authoritative ``ProtocolMachine`` and checks
    admissibility against it (FR-021/FR-062, STATE-003), so a transmitted phase
    would duplicate that authority or be uncomputable in lockstep. A
    *projection*, never an owner - the sub-game index belongs to
    ``app.orchestrator``, the step to ``domain.truth`` - validation is
    **structural only**: ``sub_game`` reads the one globally FIXED ``num_games``
    authority rather than restating six, while ``step`` has no context-free
    ceiling because ``max_moves`` is per-sub-game locked config it never carries.
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

    def __post_init__(self) -> None:
        if type(self.cursor) is not TurnCursor:
            raise ValueError(f"cursor must be a TurnCursor, got {type(self.cursor).__name__}")
        if type(self.action) not in (MoveAction, BarrierAction):
            raise ValueError(
                f"action must be a MoveAction or BarrierAction, got {type(self.action).__name__}",
            )
        if type(self.hint) is not str:
            raise ValueError(f"hint must be a str, got {type(self.hint).__name__}")


def _require_int(value: object, name: str) -> None:
    """Reject anything but a real ``int``; ``bool`` is an ``int`` and is refused.

    Accepting ``True`` as sub-game 1 would be exactly the silent coercion the
    project forbids, so the check is on the type itself, not ``isinstance``.
    """
    if type(value) is not int:
        raise ValueError(f"{name} must be an int, got {type(value).__name__}")
