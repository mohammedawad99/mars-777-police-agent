"""Reading the disclosed capture transcript out of an untrusted document.

The sealed entries and this transcript are two different kinds of evidence. An
entry is bound to a `H_commit` and cannot be rewritten without failing SHA-256;
a capture row is bound to nothing at all, because a claim and its answer were
never members of the commitment. That is precisely why the row is retained live
and compared here - the document is the peer's *story* about the questions it
asked and was asked, and the only thing that makes it evidence is that both
sides kept the real one.

So this module parses and refuses; it never decides. `capture_transcript`
compares what it returns against what was observed, and `semantic_capture`
recomputes what the answers should have been.
"""

from .audit_json import mapping, point, refuse, text, whole
from .capture_transcript import CaptureRecord
from .capture_values import CaptureAnswer, CaptureClaim
from .turn_cursor import TurnCursor


def capture_rows(document: dict[str, object]) -> tuple[CaptureRecord, ...]:
    """Every disclosed capture row, as immutable values in the order given.

    A document with no `capture` member is refused rather than read as an empty
    transcript: "I asked and answered nothing" is a claim about a whole
    sub-game, and a peer must make it explicitly to have it checked.
    """
    listing = document.get("capture")
    if not isinstance(listing, list):
        raise refuse("has no 'capture' transcript")
    sub_game = whole(document, "sub_game")
    return tuple(_row(mapping(item, "capture row"), sub_game) for item in listing)


def _row(row: dict[str, object], sub_game: int) -> CaptureRecord:
    """One transcript row, bound to the sub-game the document identifies."""
    return CaptureRecord(
        TurnCursor(sub_game, whole(row, "step")),
        _claim(row.get("claim")),
        _answer(text(row, "answer")),
    )


def _claim(value: object) -> CaptureClaim | None:
    """The declared cell, or `None` when this turn declared nothing."""
    if value is None:
        return None
    return CaptureClaim(point(value, "capture claim"))


def _answer(token: str) -> CaptureAnswer:
    """The answer, refusing anything outside the closed vocabulary."""
    try:
        return CaptureAnswer(token)
    except ValueError:
        raise refuse(f"carries an unknown capture answer {token!r}") from None
