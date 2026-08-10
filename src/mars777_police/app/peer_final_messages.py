"""The end-of-sub-game and end-of-series peer-visible message families.

``FinalNonceReveal`` closes the commit-reveal cycle for one sub-game;
``ResultAgreement`` closes the series. Both are immutable semantic values: they
open no socket, compute no digest and read no clock.

``ResultAgreement`` deliberately carries **no** ``result_sha256``. The common
digest cannot exist until a peer holds the opponent's contribution, so it is the
operation's *response* - the already-existing ``Sha256Digest`` - and never a
member of the request (`RESULT_CONTRACT.md` §R13-R2-2/-5).
"""

from dataclasses import dataclass

from .artifact_values import UtcTimestamp
from .protocol_values import NonceValue
from .result_values import InvalidResultValueError, ResultContribution
from .turn_cursor import TurnCursor

DECLARATION_FILENAME = "declaration_{game_id}.json"
"""The official Table-20 declaration filename the result joins against."""


@dataclass(frozen=True, slots=True)
class NonceRevealEntry:
    """One revealed nonce bound to the turn whose commitment it opens.

    Association only. The cursor says *which* sealed turn, the nonce completes
    the material an auditor needs beside what was already revealed - and nothing
    else belongs here, because every other fact is already owned elsewhere.
    """

    cursor: TurnCursor
    nonce: NonceValue

    def __post_init__(self) -> None:
        if type(self.cursor) is not TurnCursor:
            raise ValueError(f"cursor must be a TurnCursor, got {type(self.cursor).__name__}")
        if type(self.nonce) is not NonceValue:
            raise ValueError(f"nonce must be a NonceValue, got {type(self.nonce).__name__}")


@dataclass(frozen=True, slots=True)
class FinalNonceReveal:
    """The peer-visible final reveal: this side's nonces for one sub-game.

    An exact ``tuple`` of entries and nothing more - no ``sub_game`` field, since
    every entry's cursor carries it, and no ``role``. The tuple is taken as given:
    a list, set or generator is refused rather than converted, so the represented
    sequence is never silently reordered or consumed.

    An **empty batch is structurally valid**. Whether it is *complete* depends on
    the steps actually played, which is exactly why that check is LIVE - as are
    duplicate cursors, ordering and mixed sub-games, all accepted here.
    """

    entries: tuple[NonceRevealEntry, ...]

    def __post_init__(self) -> None:
        if type(self.entries) is not tuple:
            raise ValueError(f"entries must be a tuple, got {type(self.entries).__name__}")
        for entry in self.entries:
            if type(entry) is not NonceRevealEntry:
                raise ValueError(
                    f"every entry must be a NonceRevealEntry, got {type(entry).__name__}",
                )


@dataclass(frozen=True, slots=True)
class ResultAgreement:
    """Timeline event 14: one peer's half of the mutual result agreement.

    Identity first, the shared agreement ``timestamp`` next, the sender's own
    contribution last. The timestamp is stored, never chosen here: which peer
    proposes it and how the two requests are ordered is application protocol.

    ``declaration_ref`` is checked against ``game_id`` because both live inside
    this one immutable value and the Table-20 join is already frozen - a
    reference naming another game is self-contradictory before any artifact is
    opened. Whether that declaration exists, and whether the contributed commit
    matches it, are LIVE duties.
    """

    game_id: str
    game_uid: str
    declaration_ref: str
    timestamp: UtcTimestamp
    contribution: ResultContribution

    def __post_init__(self) -> None:
        for name, text in (
            ("game_id", self.game_id),
            ("game_uid", self.game_uid),
            ("declaration_ref", self.declaration_ref),
        ):
            if type(text) is not str:
                raise InvalidResultValueError(
                    f"{name} must be a str, got {type(text).__name__}",
                )
            if not text:
                raise InvalidResultValueError(f"{name} must be non-empty")
        expected = DECLARATION_FILENAME.format(game_id=self.game_id)
        if self.declaration_ref != expected:
            raise InvalidResultValueError(
                f"declaration_ref must be {expected!r}, got {self.declaration_ref!r};"
                " it is never trimmed, path-qualified or renamed",
            )
        if type(self.timestamp) is not UtcTimestamp:
            raise InvalidResultValueError(
                f"timestamp must be a UtcTimestamp, got {type(self.timestamp).__name__}",
            )
        if type(self.contribution) is not ResultContribution:
            raise InvalidResultValueError(
                "contribution must be a ResultContribution, got"
                f" {type(self.contribution).__name__}",
            )
