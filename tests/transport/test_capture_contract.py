"""The capture claim and the turn outcome, through the real codecs.

The claim is REFERENCE-COMPATIBLE (`capture_claim: [row, col]`, `null` when no
claim was made); the outcome is PROJECT-CONTRACT, because the lecturer reference
answers on a later message instead of returning one.
"""

import pytest
from peer_ops import CURSOR

from mars777_police.app.capture_values import (
    CaptureAnswer,
    CaptureClaim,
    InvalidCaptureError,
    TurnOutcome,
)
from mars777_police.app.peer_turn_messages import Reveal
from mars777_police.app.protocol_errors import MalformedMessageError
from mars777_police.domain.actions import MoveAction
from mars777_police.domain.board import Position
from mars777_police.domain.rules import Move
from mars777_police.transport.codec_turn import (
    decode_outcome,
    decode_reveal,
    encode_outcome,
    encode_reveal,
)
from mars777_police.transport.wire_turn import TurnOutcomeWire

CELL = Position(3, 4)


def claimed() -> Reveal:
    """A police reveal that declares its post-action cell holds the thief."""
    return Reveal(CURSOR, MoveAction(Move.N), "closing in", CaptureClaim(CELL))


def test_a_claim_round_trips_through_the_reference_row_col_shape() -> None:
    wire = encode_reveal(claimed())
    assert wire.capture_claim == [3, 4]
    assert decode_reveal(wire) == claimed()


def test_a_reveal_without_a_claim_carries_null_and_no_nonce() -> None:
    wire = encode_reveal(Reveal(CURSOR, MoveAction(Move.N), "quiet turn"))
    document = wire.model_dump(mode="json")
    assert document["capture_claim"] is None
    assert "nonce" not in str(document) and "state" not in document
    assert decode_reveal(wire).capture_claim is None


@pytest.mark.parametrize("broken", [[1], [1, 2, 3], []])
def test_a_claim_that_is_not_one_cell_is_refused(broken: list[int]) -> None:
    wire = encode_reveal(claimed())
    wire.capture_claim = broken
    with pytest.raises(MalformedMessageError, match="row, col"):
        decode_reveal(wire)


def test_a_claim_needs_a_real_position() -> None:
    with pytest.raises(InvalidCaptureError, match="Position"):
        CaptureClaim((3, 4))  # type: ignore[arg-type]


@pytest.mark.parametrize("answer", list(CaptureAnswer))
def test_every_answer_round_trips_and_only_caught_ends_the_sub_game(
    answer: CaptureAnswer,
) -> None:
    outcome = TurnOutcome(True, answer)
    assert decode_outcome(encode_outcome(outcome)) == outcome
    assert outcome.caught is (answer is CaptureAnswer.CAUGHT)


def test_an_answer_outside_the_vocabulary_is_refused() -> None:
    with pytest.raises(MalformedMessageError, match="unknown capture answer"):
        decode_outcome(TurnOutcomeWire(accepted=True, capture="MAYBE"))


def test_the_outcome_carries_exactly_the_two_frozen_members() -> None:
    from dataclasses import fields

    assert [field.name for field in fields(TurnOutcome)] == ["accepted", "capture"]
    assert set(TurnOutcomeWire.model_fields) == {"accepted", "capture"}
    for absent in ("position", "cell", "state", "nonce", "reason", "verified"):
        assert absent not in TurnOutcomeWire.model_fields


@pytest.mark.parametrize(("accepted", "capture"), [("yes", CaptureAnswer.CAUGHT), (True, "CAUGHT")])
def test_the_outcome_refuses_anything_but_its_frozen_types(
    accepted: object, capture: object
) -> None:
    with pytest.raises(InvalidCaptureError):
        TurnOutcome(accepted, capture)  # type: ignore[arg-type]


def test_a_claim_is_not_a_sealed_member() -> None:
    """It rides the request; the eight-field commitment is untouched."""
    from mars777_police.protocol.commitment import build_sealed_record

    sealed = build_sealed_record.__doc__ or ""
    assert "capture" not in sealed.lower()
