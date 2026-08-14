"""What our own reveal deposited, kept by the side that sent it.

The receiver has held the peer's emission since Reveal V2 - `TurnEvidence.scent`
is the inbound authority and stays it. The sender held nothing: the emission went
out on the wire and was gone, so at the final audit there was no history to
disclose from and the only way to produce one would have been to project it again
from the action, which is exactly the rewrite the audit is supposed to detect.

So the transcript that already keeps our capture rows keeps this too, copied out
of the very `Reveal` being recorded. One tuple, outbound only: a second inbound
collection would be a second history of the same fact, free to drift from the one
that was witnessed.
"""

import dataclasses

import pytest
import turn_builders as build
from turn_builders import START, advanced, legal_reveal, runtime

from mars777_police.app.capture_transcript import TurnTranscript
from mars777_police.app.capture_values import CaptureAnswer, TurnOutcome
from mars777_police.app.interop_profiles import CompatibilityProfile
from mars777_police.app.peer_turn_messages import Reveal
from mars777_police.app.scent_records import ScentRecord
from mars777_police.app.turn_cursor import TurnCursor
from mars777_police.domain.actions import MoveAction
from mars777_police.domain.rules import Move

V1 = CompatibilityProfile.STRICT_COUNTED_MATCH_TURN_OUTCOME_V1
ANSWERED = TurnOutcome(True, CaptureAnswer.NO_QUESTION)


def legacy_reveal(cursor: TurnCursor = START) -> Reveal:
    """A pre-V2 reveal: the same turn, carrying no emission at all."""
    return Reveal(cursor, MoveAction(Move.N), "heading north")


def test_the_transcript_keeps_exactly_one_outbound_scent_tuple() -> None:
    names = tuple(field.name for field in dataclasses.fields(TurnTranscript))
    assert names == ("inbound", "outbound", "declared", "sent_scent")
    assert "inbound_scent" not in names and "received_scent" not in names


def test_sending_a_v2_reveal_retains_exactly_what_it_carried() -> None:
    live, reveal = TurnTranscript(), legal_reveal()
    live.observe_outgoing(reveal, ANSWERED)
    assert live.sent_scent == (ScentRecord(START, reveal.scent_emission),)
    assert live.sent_scent[0].emission is reveal.scent_emission, "the object, not a copy"


def test_the_row_is_written_once_per_reveal() -> None:
    live = TurnTranscript()
    live.observe_outgoing(legal_reveal(), ANSWERED)
    live.observe_outgoing(legal_reveal(TurnCursor(1, 2)), ANSWERED)
    assert len(live.sent_scent) == 2
    assert [row.cursor.step for row in live.sent_scent] == [1, 2]


def test_a_legacy_reveal_leaves_no_scent_row_at_all() -> None:
    live = TurnTranscript()
    live.observe_outgoing(legacy_reveal(), ANSWERED)
    assert live.sent_scent == ()


def test_the_capture_row_is_still_written_either_way() -> None:
    """Orthogonal: adding scent changed nothing about the capture transcript."""
    with_scent, without = TurnTranscript(), TurnTranscript()
    with_scent.observe_outgoing(legal_reveal(), ANSWERED)
    without.observe_outgoing(legacy_reveal(), ANSWERED)
    assert with_scent.outbound == without.outbound
    assert len(with_scent.outbound) == 1 and with_scent.outbound[0].cursor == START


def test_an_inbound_reveal_writes_no_outbound_scent() -> None:
    """The two directions never cross: what arrives is not what we sent."""
    live = TurnTranscript()
    live.observe_inbound(legal_reveal(), ANSWERED)
    assert live.sent_scent == () and len(live.inbound) == 1


def test_the_live_runtime_keeps_the_peers_emission_where_it_always_did() -> None:
    live = advanced(runtime())
    reveal = legal_reveal()
    live.accept_reveal(reveal)
    (witnessed,) = live.evidence
    assert witnessed.scent is reveal.scent_emission
    assert live.capture.sent_scent == (), "an inbound reveal is not one of ours"


def test_our_own_reveal_is_retained_by_the_runtime_that_sent_it() -> None:
    live = advanced(runtime())
    ours = legal_reveal()
    live.observe_outgoing(ours, ANSWERED)
    assert live.capture.sent_scent == (ScentRecord(START, ours.scent_emission),)
    assert live.evidence == (), "our own reveal is never opponent observation"


def test_the_retained_emission_is_never_reprojected_from_the_action() -> None:
    """A hand-supplied emission survives untouched: nothing recomputes it here."""
    elsewhere = build.emission(build.BLOCKED)
    reveal = Reveal(START, MoveAction(Move.N), "north", None, elsewhere)
    live = TurnTranscript()
    live.observe_outgoing(reveal, ANSWERED)
    assert live.sent_scent[0].emission == elsewhere
    assert elsewhere != build.emission(), "the model would have produced the other one"


@pytest.mark.parametrize("posture", [V1, CompatibilityProfile.STRICT_COUNTED_MATCH])
def test_the_retention_is_posture_blind_because_the_reveal_already_decided(
    posture: CompatibilityProfile,
) -> None:
    """The gate that refuses a wrong-posture reveal runs earlier, on the way in."""
    live = dataclasses.replace(runtime(), posture=posture)
    live.observe_outgoing(legacy_reveal(), ANSWERED)
    assert live.capture.sent_scent == ()
