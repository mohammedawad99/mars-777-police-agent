"""Reveal: `True`/`False` for legality only, everything else raises.

The distinction this file exists to hold: a protocol failure and an illegal move
are different answers to different questions, and the boolean is reserved for
the second.
"""

import pytest
from turn_builders import (
    START,
    advanced,
    commitment,
    illegal_reveal,
    legal_reveal,
    runtime,
)

from mars777_police.app.protocol_errors import StaleMessageError
from mars777_police.app.turn_cursor import TurnCursor
from mars777_police.app.turn_protocol_state import TurnPhase


def test_a_legal_revealed_action_returns_true() -> None:
    live = advanced(runtime())
    assert live.accept_reveal(legal_reveal()) is True
    assert live.phase is TurnPhase.CONSUMED


def test_a_game_illegal_revealed_action_returns_false() -> None:
    """The real barrier rules refuse it; the protocol was still valid."""
    live = advanced(runtime())
    assert live.accept_reveal(illegal_reveal()) is False
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
    assert live.accept_reveal(legal_reveal()) is True
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


def test_a_legal_reveal_mutates_truth_exactly_once_and_advances_the_step() -> None:
    live = advanced(runtime())
    before = live.truth
    live.accept_reveal(legal_reveal())
    assert live.truth is not before
    assert live.truth.completed_steps == before.completed_steps + 1
    assert live.cursor == TurnCursor(START.sub_game, live.truth.completed_steps)


def test_an_illegal_reveal_leaves_truth_and_the_cursor_untouched() -> None:
    """Exactly `LocalTurnService` semantics: a refused action produces no truth."""
    live = advanced(runtime())
    before, cursor = live.truth, live.cursor
    assert live.accept_reveal(illegal_reveal()) is False
    assert live.truth is before
    assert live.cursor == cursor


def test_the_hint_is_carried_but_decides_nothing() -> None:
    """Two hints, same action, same verdict - language never moves a piece."""
    from mars777_police.app.peer_turn_messages import Reveal

    first = advanced(runtime())
    second = advanced(runtime())
    action = legal_reveal().action
    assert first.accept_reveal(Reveal(START, action, "north, honestly")) is True
    assert second.accept_reveal(Reveal(START, action, "south, dishonestly")) is True
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
