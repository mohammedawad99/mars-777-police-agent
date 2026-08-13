"""The retained transcript, and every way a peer could retell it differently.

A capture row is not a member of `H_commit`, so nothing cryptographic stops a
peer from disclosing a different story than the one it told live. What stops it
is that both sides kept the real rows: the comparison below is ordered and
total, so an added row, a missing one, a duplicate, a reordering, a moved cursor,
a claim that appeared or vanished and a rewritten answer all fail alike.
"""

import pytest

from mars777_police.app.capture_transcript import (
    CaptureRecord,
    TranscriptMismatchError,
    TurnTranscript,
    require_same_transcript,
)
from mars777_police.app.capture_values import CaptureAnswer, CaptureClaim, TurnOutcome
from mars777_police.app.peer_turn_messages import Reveal
from mars777_police.app.protocol_errors import StaleMessageError
from mars777_police.app.turn_cursor import TurnCursor
from mars777_police.domain.actions import MoveAction
from mars777_police.domain.board import Position
from mars777_police.domain.rules import Move

HERE = Position(2, 3)
NORTH = MoveAction(Move.N)
CAUGHT, NOT_CAUGHT, QUIET = (
    CaptureAnswer.CAUGHT,
    CaptureAnswer.NOT_CAUGHT,
    CaptureAnswer.NO_QUESTION,
)


def record(
    step: int, answer: CaptureAnswer = QUIET, claim: Position | None = None
) -> CaptureRecord:
    return CaptureRecord(
        TurnCursor(1, step), None if claim is None else CaptureClaim(claim), answer
    )


OBSERVED = (record(1), record(2, CAUGHT, HERE))


def reveal(step: int, claim: Position | None = None) -> Reveal:
    return Reveal(
        TurnCursor(1, step), NORTH, "closing in", None if claim is None else CaptureClaim(claim)
    )


def test_a_rewritten_transcript_leaves_by_the_existing_stale_identity() -> None:
    """The peer contradicted itself, so it is a peer failure with no new code."""
    assert issubclass(TranscriptMismatchError, StaleMessageError)
    assert TranscriptMismatchError.error_id == "E-PROTO-STALE"


def test_the_transcript_that_was_observed_is_accepted() -> None:
    assert require_same_transcript(OBSERVED, tuple(OBSERVED)) is None


def test_an_added_row_is_refused() -> None:
    with pytest.raises(TranscriptMismatchError, match="3 rows"):
        require_same_transcript(OBSERVED, (*OBSERVED, record(3)))


def test_a_removed_row_is_refused() -> None:
    with pytest.raises(TranscriptMismatchError, match="2 turns were actually answered"):
        require_same_transcript(OBSERVED, OBSERVED[:1])


def test_a_rewritten_answer_is_refused() -> None:
    with pytest.raises(TranscriptMismatchError, match=r"row for TurnCursor\(sub_game=1, step=2\)"):
        require_same_transcript(OBSERVED, (OBSERVED[0], record(2, NOT_CAUGHT, HERE)))


def test_a_claim_that_vanished_is_refused() -> None:
    with pytest.raises(TranscriptMismatchError, match="is not the one observed"):
        require_same_transcript(OBSERVED, (OBSERVED[0], record(2, CAUGHT)))


def test_a_claim_that_appeared_is_refused() -> None:
    with pytest.raises(TranscriptMismatchError, match="is not the one observed"):
        require_same_transcript(OBSERVED, (record(1, QUIET, HERE), OBSERVED[1]))


def test_a_claim_moved_to_another_cell_is_refused() -> None:
    with pytest.raises(TranscriptMismatchError, match="is not the one observed"):
        require_same_transcript(OBSERVED, (OBSERVED[0], record(2, CAUGHT, Position(4, 4))))


def test_a_duplicated_row_is_refused() -> None:
    with pytest.raises(TranscriptMismatchError):
        require_same_transcript(OBSERVED, (OBSERVED[0], OBSERVED[0]))


def test_a_reordered_transcript_is_refused() -> None:
    with pytest.raises(TranscriptMismatchError, match="is not the one observed"):
        require_same_transcript(OBSERVED, (OBSERVED[1], OBSERVED[0]))


def test_a_row_moved_to_another_cursor_is_refused() -> None:
    with pytest.raises(TranscriptMismatchError, match="is not the one observed"):
        require_same_transcript(OBSERVED, (OBSERVED[0], record(3, CAUGHT, HERE)))


@pytest.mark.parametrize(
    ("cursor", "claim", "answer", "expected"),
    [
        ((1, 1), None, QUIET, "needs a TurnCursor"),
        (TurnCursor(1, 1), HERE, QUIET, "must be a CaptureClaim"),
        (TurnCursor(1, 1), None, "CAUGHT", "must be a CaptureAnswer"),
    ],
)
def test_a_row_is_built_from_real_values_or_not_at_all(
    cursor: object, claim: object, answer: object, expected: str
) -> None:
    """A local construction defect, so a plain `ValueError` - not a peer failure."""
    with pytest.raises(ValueError, match=expected):
        CaptureRecord(cursor, claim, answer)  # type: ignore[arg-type]


def test_the_two_directions_are_kept_apart() -> None:
    transcript = TurnTranscript()
    transcript.observe_inbound(reveal(1), TurnOutcome(True, QUIET))
    transcript.observe_outgoing(reveal(1, HERE), TurnOutcome(True, CAUGHT))
    assert transcript.inbound == (record(1),)
    assert transcript.outbound == (record(1, CAUGHT, HERE),)


def test_a_declared_capture_is_remembered_from_either_direction() -> None:
    inbound, outbound = TurnTranscript(), TurnTranscript()
    inbound.observe_inbound(reveal(1), TurnOutcome(True, QUIET))
    outbound.observe_outgoing(reveal(1), TurnOutcome(True, QUIET))
    assert (inbound.declared, outbound.declared) == (False, False)
    inbound.observe_inbound(reveal(2, HERE), TurnOutcome(True, NOT_CAUGHT))
    outbound.observe_outgoing(reveal(2, HERE), TurnOutcome(True, NOT_CAUGHT))
    assert inbound.declared and outbound.declared
