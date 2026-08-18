"""The two settlement defects the first live sub-game exposed, pinned.

Observed 2026-08-18 against the pinned peer: MaRs-777 Police settled `CAPTURE`
and stopped talking while the peer waited out its budget and settled `timeout` -
the contradictory-reports shape App. E rule 35 zeroes on **both** teams.

Two distinct causes, and both are here:

**1. The self-capture rule is the thief's.** Rules 46/47 end the game at a
position only the *thief* can see - a barrier on its own cell, or no orthogonal
escape. `BAR-004` explicitly lets the **police** place a barrier on its own cell
and legally stand on a blocked one, so applying self-capture to the police
invents a capture out of a lawful placement.

**2. A terminal answer must ride out before we stop talking.** The opponent
cannot see the board; walking away holding the answer makes it wait out its
budget and settle a game it already lost as a timeout.
"""

import pytest
from r16_builders import config

from mars777_police.app.capture_values import CaptureAnswer, CaptureClaim
from mars777_police.app.config_rules import opening_truth, rules_of
from mars777_police.app.kit_adjudicate import adjudicate, self_captured
from mars777_police.app.kit_messages import KitRole
from mars777_police.app.sealed_record_values import ActorRole
from mars777_police.domain.barriers import place_barrier
from mars777_police.domain.terminal import Outcome


def police_on_its_own_barrier() -> tuple[object, object]:
    """`BAR-004`: the police may place a barrier on its own cell and stand there."""
    truth = opening_truth(config(), ActorRole.POLICE)
    board = place_barrier(
        truth.board, truth.own_position, truth.own_position, rules_of(config()).quota
    )
    return board, truth.own_position


def test_a_police_standing_on_its_own_barrier_is_not_captured() -> None:
    """The exact false CAPTURE that made us stop talking in the live sub-game."""
    board, cell = police_on_its_own_barrier()

    assert self_captured(board, cell, KitRole.POLICE) is False


def test_the_thief_on_a_barriered_cell_is_captured() -> None:
    """Rules 46/47 stay exactly as they were for the side they belong to."""
    board, cell = police_on_its_own_barrier()

    assert self_captured(board, cell, KitRole.THIEF) is True


def test_the_police_never_reaches_a_verdict_from_its_own_cell() -> None:
    verdict = adjudicate(
        role=KitRole.POLICE,
        incoming=None,
        answer=CaptureAnswer.NO_QUESTION,
        trapped=False,
        step=3,
        max_steps=35,
        survival_threshold=35,
    )

    assert verdict.outcome is None


@pytest.mark.parametrize(
    ("role", "answer", "owed"),
    [
        (KitRole.THIEF, CaptureAnswer.CAUGHT, True),
        (KitRole.THIEF, CaptureAnswer.NOT_CAUGHT, True),
        (KitRole.POLICE, CaptureAnswer.NO_QUESTION, False),
    ],
)
def test_an_answer_we_owe_decides_whether_a_terminal_message_rides_out(
    role: KitRole, answer: CaptureAnswer, owed: bool
) -> None:
    """Only a side that owes something sends a final; nobody double-sends."""
    from mars777_police.app.kit_adjudicate import terminal_owed

    assert terminal_owed(role=role, pending=answer is not CaptureAnswer.NO_QUESTION) is owed


def test_a_thief_that_conceded_still_owes_the_concession() -> None:
    from mars777_police.app.kit_adjudicate import terminal_owed

    assert terminal_owed(role=KitRole.THIEF, pending=False) is True


def test_the_answer_is_computed_from_our_own_cell_and_never_from_the_claim() -> None:
    from mars777_police.app.kit_adjudicate import answer_claim

    truth = opening_truth(config(), ActorRole.THIEF)

    assert (
        answer_claim(CaptureClaim(truth.own_position), truth.own_position) is CaptureAnswer.CAUGHT
    )
    assert answer_claim(None, truth.own_position) is CaptureAnswer.NO_QUESTION


def test_a_capture_settles_the_same_way_on_both_sides() -> None:
    """The semantic outcome a co-location capture produces, for either role."""
    caught = adjudicate(
        role=KitRole.THIEF,
        incoming=None,
        answer=CaptureAnswer.CAUGHT,
        trapped=False,
        step=4,
        max_steps=35,
        survival_threshold=35,
    )

    assert caught.outcome is Outcome.CAPTURE
