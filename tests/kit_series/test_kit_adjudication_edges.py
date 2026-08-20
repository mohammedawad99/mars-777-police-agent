"""The endings only one side can see, decided from the board alone.

Nothing here sends a message. Each case hands the adjudicator a position it is
supposed to have an opinion about - a thief with nowhere legal to go, an
exhausted step ceiling, a grid our domain cannot represent - and pins the
verdict, including the one where the honest answer is silence.
"""

import pytest
from r16_builders import config

from mars777_police.__main__ import ROLE
from mars777_police.app.capture_values import CaptureAnswer
from mars777_police.app.commitment_codecs import CommitmentCodec
from mars777_police.app.kit_adjudicate import adjudicate
from mars777_police.app.kit_messages import KitRole
from mars777_police.app.kit_play import KitPlayState, peer_belief
from mars777_police.app.kit_records import KitRecordChain
from mars777_police.app.protocol_errors import StaleMessageError
from mars777_police.app.sealed_record_values import Intent
from mars777_police.app.turn_cursor import TurnCursor
from mars777_police.domain.actions import MoveAction
from mars777_police.domain.rules import Move
from mars777_police.domain.scent_belief import NO_SCENT
from mars777_police.domain.terminal import Outcome
from mars777_police.protocol.secure_nonce import SecretsNonceSource

OURS = KitRole(ROLE.value)


def test_a_thief_that_cannot_move_reaches_the_ending_only_it_can_see() -> None:
    verdict = adjudicate(
        role=KitRole.THIEF,
        incoming=None,
        answer=CaptureAnswer.NO_QUESTION,
        trapped=True,
        step=3,
        max_steps=35,
        survival_threshold=35,
    )

    assert verdict.outcome is Outcome.CAPTURE
    assert verdict.reason


def test_the_step_ceiling_ends_an_uncaught_thief_s_sub_game() -> None:
    verdict = adjudicate(
        role=KitRole.THIEF,
        incoming=None,
        answer=CaptureAnswer.NO_QUESTION,
        trapped=False,
        step=35,
        max_steps=35,
        survival_threshold=40,
    )

    assert verdict.outcome is Outcome.SURVIVAL


def test_a_grid_our_domain_cannot_hold_is_silence_rather_than_a_belief() -> None:
    board = KitPlayState.opening(config(), ROLE).truth.board

    assert peer_belief((("nonsense", 0.5),), board) is NO_SCENT
    assert peer_belief((("99,99", 0.5),), board) is NO_SCENT


def test_a_chain_seals_nothing_once_the_opponent_holds_its_nonces() -> None:
    chain = KitRecordChain(CommitmentCodec.KIT_CORE_COMMITMENT_V1, SecretsNonceSource())
    chain.reveal(
        OURS,
        __import__(
            "mars777_police.app.kit_messages", fromlist=["KitResultClaim"]
        ).KitResultClaim.SURVIVAL,
    )

    with pytest.raises(StaleMessageError):
        chain.seal(
            cursor=TurnCursor(1, 1),
            role=ROLE,
            action=MoveAction(Move.STAY),
            intent=next(iter(Intent)),
            hint="",
            own_position=KitPlayState.opening(config(), ROLE).truth.own_position,
            barriers=(),
        )
