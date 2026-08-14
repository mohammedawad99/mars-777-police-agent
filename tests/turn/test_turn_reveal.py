"""Reveal: the outcome the receiver can honestly report, everything else raises.

Stage 5-R8 replaced the legality bool. The receiver never learns the mover's
sealed pre-action cell, so it cannot decide whether their move was spatially
legal - that is proved at the final audit. What it reports live is public-fact
acceptance plus the capture answer, and the peer's action never moves our piece.
"""

import pytest
import turn_builders
from turn_builders import (
    START,
    advanced,
    commitment,
    illegal_reveal,
    legal_reveal,
    runtime,
)

from mars777_police.app.capture_values import CaptureAnswer, TurnOutcome
from mars777_police.app.protocol_errors import StaleMessageError
from mars777_police.app.turn_cursor import TurnCursor
from mars777_police.app.turn_protocol_state import TurnPhase


def test_a_revealed_move_is_accepted_and_asks_no_capture_question() -> None:
    live = advanced(runtime())
    outcome = live.accept_reveal(legal_reveal())
    assert outcome == TurnOutcome(True, CaptureAnswer.NO_QUESTION)
    assert live.phase is TurnPhase.CONSUMED


def test_a_move_the_receiver_cannot_check_is_still_accepted_live() -> None:
    """Their pre-action cell is sealed, so we do not pretend to judge it."""
    live = advanced(runtime())
    outcome = live.accept_reveal(illegal_reveal())
    assert outcome.accepted is True
    assert outcome.capture is CaptureAnswer.NO_QUESTION
    assert live.phase is TurnPhase.CONSUMED


def test_a_reveal_before_any_commitment_raises_rather_than_returning_false() -> None:
    with pytest.raises(StaleMessageError) as raised:
        runtime().accept_reveal(legal_reveal())
    assert raised.value.error_id == "E-PROTO-STALE"


def test_a_reveal_before_acknowledgement_raises() -> None:
    live = runtime()
    live.accept_commitment(commitment())
    with pytest.raises(StaleMessageError, match="cannot arrive"):
        live.accept_reveal(legal_reveal())


def test_a_reveal_for_another_cursor_raises() -> None:
    live = advanced(runtime())
    with pytest.raises(StaleMessageError):
        live.accept_reveal(legal_reveal(TurnCursor(1, 4)))


def test_a_duplicate_reveal_is_refused_and_never_replays_the_action() -> None:
    """The critical anti-replay property: a repeat cannot move a second time."""
    live = advanced(runtime())
    assert live.accept_reveal(legal_reveal()).accepted is True
    moved_once = live.truth.own_position
    steps_once = live.truth.completed_steps
    with pytest.raises(StaleMessageError, match="cannot arrive"):
        live.accept_reveal(legal_reveal())
    assert live.truth.own_position == moved_once
    assert live.truth.completed_steps == steps_once


def test_a_protocol_invalid_reveal_never_reaches_the_game() -> None:
    """Ordering is checked before legality, so truth cannot move out of order."""
    live = runtime()
    before = live.truth
    with pytest.raises(StaleMessageError):
        live.accept_reveal(legal_reveal())
    assert live.truth is before
    assert live.evidence == ()


def test_a_peer_move_never_moves_our_own_piece() -> None:
    """The R8 defect removal: their movement is theirs, not ours."""
    live = advanced(runtime())
    before, cursor = live.truth, live.cursor
    live.accept_reveal(legal_reveal())
    assert live.truth is before
    assert live.truth.own_position == before.own_position
    assert live.truth.completed_steps == before.completed_steps
    assert live.cursor == cursor


def test_a_move_we_cannot_judge_leaves_truth_and_the_cursor_untouched() -> None:
    live = advanced(runtime())
    before, cursor = live.truth, live.cursor
    assert live.accept_reveal(illegal_reveal()).accepted is True
    assert live.truth is before
    assert live.cursor == cursor


def test_the_hint_is_carried_but_decides_nothing() -> None:
    """Two hints, same action, same verdict - language never moves a piece."""
    from mars777_police.app.peer_turn_messages import Reveal

    first = advanced(runtime())
    second = advanced(runtime())
    action = legal_reveal().action
    emission = turn_builders.emission()
    assert first.accept_reveal(Reveal(START, action, "north, honestly", None, emission)).accepted
    assert second.accept_reveal(
        Reveal(START, action, "south, dishonestly", None, emission)
    ).accepted
    assert first.evidence[0].hint != second.evidence[0].hint


def test_the_stored_commitment_always_matches_a_validated_reveal() -> None:
    """Why `accept_reveal` needs no separate commitment-correlation branch.

    The commitment is stored only when its cursor equals the runtime's, the
    reveal is refused unless its cursor equals the runtime's, and nothing moves
    the cursor in between - so by the time the reveal is applied the two are
    necessarily the same object's cursor. Deleting the unreachable branch is
    sound because of this, not despite it.
    """
    live = advanced(runtime())
    pending = live.peer_commitment
    assert pending is not None
    assert pending.cursor == live.cursor
    assert pending.matches(live.cursor)
    live.accept_reveal(legal_reveal())
    assert live.evidence[0].cursor == pending.cursor
