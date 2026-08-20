"""What a replay shows a reader, as small immutable values.

The Replay Viewer projects; it decides nothing. Every verdict in these values
came from an authority that already existed - `domain.rules` for legality,
`app.semantic_replay` for trajectory consistency, the commitment codec for the
digest - and is carried here unchanged so a reader sees the same answer the
audit saw.

**The two crypto words are the book's own.** `REPLAY-002` requires the viewer to
show `Verified OK` on a match and `TAMPERED` on any mismatch, so those are the
literals, not a paraphrase. The two other statuses exist because collapsing them
into `Verified OK` would be a lie: evidence that was never applicable and
evidence that cannot be checked are different from evidence that verified.
"""

from dataclasses import dataclass
from enum import StrEnum


class ReplayError(Exception):
    """The viewer cannot read or replay this evidence, and says why."""


class ReplayCheck(StrEnum):
    """The cryptographic status of one replayed record."""

    VERIFIED_OK = "Verified OK"
    """The recomputed digest equals the stored commitment (REPLAY-002)."""

    TAMPERED = "TAMPERED"
    """The recomputed digest differs. Immediate disqualification, no appeal."""

    NOT_APPLICABLE = "NOT_APPLICABLE"
    """This record carries no commitment to check - an acknowledgement, say.

    Not reachable for a projected turn of an **official** log: `LOG_CONTRACT.md`
    marks the commitment `Required`, so a commit entry without one is corruption
    rather than a record with nothing to check. It stays in the vocabulary
    because the evidence layer this project froze at Stage 8A-1R has four words,
    and because a record with nothing to check must never be counted as a record
    that failed to check.
    """

    NOT_CHECKABLE = "NOT_CHECKABLE"
    """A commitment exists but its nonce was never disclosed to this side.

    Never rendered as `Verified OK`: missing evidence is not proof, and calling
    it tampering would be the opposite error.
    """


@dataclass(frozen=True, slots=True)
class ReplayTurn:
    """One side's turn, as the log disclosed it and the authorities judged it."""

    step: int
    role: str
    cell: tuple[int, int]
    barriers: tuple[tuple[int, int], ...]
    action: str
    hint: str | None
    intent: str | None
    capture_claim: str | None
    capture_answer: str | None
    commitment: str | None
    check: ReplayCheck


@dataclass(frozen=True, slots=True)
class ReplayStep:
    """One whole step: both sides' turns, and the board they left behind."""

    number: int
    turns: tuple[ReplayTurn, ...]
    police_cell: tuple[int, int]
    thief_cell: tuple[int, int]
    barriers: tuple[tuple[int, int], ...]
    grid_size: int
    semantic: str


@dataclass(frozen=True, slots=True)
class ReplaySummary:
    """What the whole replay establishes, and what it deliberately does not."""

    game_id: str
    game_uid: str
    sub_game: int
    config_sha256: str
    steps: int
    crypto: ReplayCheck
    recorded_result: str
    tampered_step: int | None
    semantic_verdict: str
    outcome_agrees: bool
    evidence_class: str
    notes: tuple[str, ...]
