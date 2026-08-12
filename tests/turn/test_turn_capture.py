"""What a turn runtime answers when a turn asks about capture.

Every answer here is computed from this runtime's own `LocalTruth` and the
public board. Nothing sends a position, and the peer's action never moves our
piece - the three capture routes are the only things a reveal can change.
"""

import pytest
from turn_builders import CENTRE, advanced, commitment, legal_reveal, runtime

from mars777_police.app.capture_values import CaptureAnswer, CaptureClaim
from mars777_police.app.peer_turn_messages import Reveal
from mars777_police.app.protocol_errors import StaleMessageError
from mars777_police.app.sealed_record_values import ActorRole
from mars777_police.app.turn_cursor import TurnCursor
from mars777_police.domain.actions import BarrierAction
from mars777_police.domain.board import Board, Position

START = TurnCursor(1, 1)


def thief() -> object:
    """A runtime whose peer is the police, so a claim is legal to receive."""
    return advanced(runtime(ActorRole.THIEF))


def reveal_with(claim: Position | None = None, target: Position | None = None) -> Reveal:
    """A peer reveal: a movement with an optional claim, or a barrier."""
    action = BarrierAction(target) if target is not None else legal_reveal().action
    return Reveal(START, action, "closing in", None if claim is None else CaptureClaim(claim))


def test_a_claim_on_our_cell_answers_caught() -> None:
    live = thief()
    outcome = live.accept_reveal(reveal_with(claim=live.truth.own_position))
    assert outcome.capture is CaptureAnswer.CAUGHT
    assert outcome.accepted is True
    assert live.audit_required is True


def test_a_claim_on_another_cell_answers_not_caught_and_still_ends_ordinary_play() -> None:
    """A false declaration is not a free probe: the sub-game goes to audit."""
    live = thief()
    outcome = live.accept_reveal(reveal_with(claim=Position(0, 0)))
    assert outcome.capture is CaptureAnswer.NOT_CAUGHT
    assert live.audit_required is True


def test_an_ordinary_move_asks_nothing_and_requires_no_audit() -> None:
    live = thief()
    outcome = live.accept_reveal(legal_reveal())
    assert outcome.capture is CaptureAnswer.NO_QUESTION
    assert live.audit_required is False


def test_only_the_police_may_declare_a_capture() -> None:
    live = advanced(runtime(ActorRole.POLICE))
    with pytest.raises(StaleMessageError, match="only the police"):
        live.accept_reveal(reveal_with(claim=Position(1, 1)))
    assert live.evidence == () and live.audit_required is False


def test_a_barrier_carries_no_claim_because_it_declares_its_own_target() -> None:
    live = thief()
    with pytest.raises(StaleMessageError, match="declares its own target"):
        live.accept_reveal(reveal_with(claim=CENTRE, target=CENTRE))
    assert live.evidence == ()


def test_a_barrier_on_our_cell_captures_us() -> None:
    live = thief()
    outcome = live.accept_reveal(reveal_with(target=live.truth.own_position))
    assert outcome == outcome.__class__(True, CaptureAnswer.CAUGHT)


def test_a_barrier_elsewhere_is_adopted_and_asks_nothing() -> None:
    live = thief()
    target = Position(0, 0)
    outcome = live.accept_reveal(reveal_with(target=target))
    assert outcome.capture is CaptureAnswer.NO_QUESTION
    assert live.truth.board.is_blocked(target)
    assert live.truth.own_position == CENTRE


def test_a_barrier_that_traps_us_captures_us() -> None:
    live = thief()
    here = live.truth.own_position
    walls = [cell for cell in live.truth.board.orthogonal_neighbours(here)]
    live.truth = live.truth.__class__(
        board=Board(rows=10, cols=10, blocked=frozenset(walls[:-1])),
        own_position=here,
        completed_steps=0,
    )
    outcome = live.accept_reveal(reveal_with(target=walls[-1]))
    assert outcome.capture is CaptureAnswer.CAUGHT


def test_a_barrier_off_the_board_is_not_accepted_and_changes_nothing() -> None:
    live = thief()
    before = live.truth
    outcome = live.accept_reveal(reveal_with(target=Position(99, 99)))
    assert outcome.accepted is False
    assert outcome.capture is CaptureAnswer.NO_QUESTION
    assert live.truth is before


def test_a_barrier_on_an_already_blocked_cell_is_not_accepted() -> None:
    live = thief()
    blocked = next(iter(live.truth.board.blocked))
    outcome = live.accept_reveal(reveal_with(target=blocked))
    assert outcome.accepted is False


def test_a_refused_reveal_never_records_a_claim() -> None:
    live = runtime(ActorRole.THIEF)
    live.accept_commitment(commitment())
    with pytest.raises(StaleMessageError):
        live.accept_reveal(reveal_with(claim=Position(1, 1)))
    assert live.audit_required is False
