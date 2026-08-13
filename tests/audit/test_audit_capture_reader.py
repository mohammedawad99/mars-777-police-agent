"""Reading the disclosed transcript, and the cross-check it feeds.

The reader is strict for the same reason the entries reader is: the document
comes from an opponent. What it produces is compared against rows this side
retained live, so the two halves are proved together here - a well-formed
transcript round-trips, and a rewritten one is refused by the real audit runtime
without weakening any R7 refusal.
"""

import audit_builders as build
import pytest
from audit_builders import PEER_GROUP, capture_json, document, nonce_batch, runtime

from mars777_police.app.audit_capture import capture_rows
from mars777_police.app.capture_transcript import TranscriptMismatchError
from mars777_police.app.capture_values import CaptureAnswer, CaptureClaim
from mars777_police.app.protocol_errors import MalformedMessageError
from mars777_police.app.protocol_values import FinalAuditVerdict
from mars777_police.app.turn_cursor import TurnCursor

CLAIMED = {"step": 1, "claim": [2, 3], "answer": "CAUGHT"}


def rows(*listing: object) -> tuple[object, ...]:
    """Read a transcript of exactly these rows out of a real document."""
    return capture_rows(document(capture=list(listing)))


def test_a_written_transcript_reads_back_as_the_rows_it_was_written_from() -> None:
    assert capture_rows(document()) == build.capture()


def test_a_claim_and_its_answer_survive_the_round_trip() -> None:
    (row,) = rows(CLAIMED)
    assert row.cursor == TurnCursor(build.SUB_GAME, 1)
    assert row.claim == CaptureClaim(build.POS[1])
    assert row.answer is CaptureAnswer.CAUGHT


@pytest.mark.parametrize(
    ("capture", "expected"),
    [
        (None, "has no 'capture' transcript"),
        ({"step": 1}, "has no 'capture' transcript"),
        ("[]", "has no 'capture' transcript"),
    ],
)
def test_a_document_without_a_real_transcript_is_refused(capture: object, expected: str) -> None:
    doc = document()
    doc["capture"] = capture
    with pytest.raises(MalformedMessageError, match=expected):
        capture_rows(doc)


def test_a_missing_capture_member_is_refused_rather_than_read_as_empty() -> None:
    doc = document()
    del doc["capture"]
    with pytest.raises(MalformedMessageError, match="has no 'capture' transcript"):
        capture_rows(doc)


@pytest.mark.parametrize(
    ("row", "expected"),
    [
        ("not an object", "capture row is not an object"),
        ({"claim": None, "answer": "CAUGHT"}, "has no integer 'step'"),
        ({"step": True, "claim": None, "answer": "CAUGHT"}, "has no integer 'step'"),
        ({"step": 1, "claim": None}, "has no usable 'answer'"),
        ({"step": 1, "claim": None, "answer": "MAYBE"}, "unknown capture answer 'MAYBE'"),
        ({"step": 1, "claim": [2], "answer": "CAUGHT"}, "not a two-member position"),
        ({"step": 1, "claim": ["2", "3"], "answer": "CAUGHT"}, "not an integer position"),
    ],
)
def test_a_malformed_row_is_refused(row: object, expected: str) -> None:
    with pytest.raises(MalformedMessageError, match=expected):
        rows(row)


def test_a_peer_that_rewrites_its_answers_is_refused_by_the_real_audit() -> None:
    live = runtime()
    live.accept_final_nonce_reveal(nonce_batch(), PEER_GROUP)
    rewritten = capture_json()
    rewritten[1] = {**rewritten[1], "answer": "CAUGHT", "claim": [2, 3]}
    with pytest.raises(TranscriptMismatchError, match="is not the one observed"):
        live.accept_audit_disclosure(document(capture=rewritten))
    assert live.outcome is None, "no verdict is derived from a document that was refused"


def test_a_peer_that_drops_a_whole_answered_turn_is_refused() -> None:
    live = runtime()
    live.accept_final_nonce_reveal(nonce_batch(), PEER_GROUP)
    with pytest.raises(TranscriptMismatchError, match="2 turns were actually answered"):
        live.accept_audit_disclosure(document(capture=capture_json((1,))))


def test_an_honest_transcript_still_reaches_the_ordinary_verdict() -> None:
    """The new check is an addition: a truthful peer audits exactly as before."""
    live = build.audited()
    assert live.verdict is FinalAuditVerdict.VERIFIED_OK
    assert live.capture == build.capture()
