"""What a sub-game delivers before it settles, and that it settles once.

The loop owes the peer exactly what the protocol says it owes - no more, and not
twice. A silent opponent is refused rather than scored, because a missing turn
is not a forfeit we may award ourselves.
"""

import asyncio

import pytest
from kit_turn_doubles import maker, peer_turn
from r16_builders import config

from mars777_police.__main__ import ROLE
from mars777_police.app.commitment_codecs import CommitmentCodec
from mars777_police.app.config_rules import limits_of
from mars777_police.app.kit_inbox import KitTurnInbox
from mars777_police.app.kit_messages import KitRole, KitTurn
from mars777_police.app.kit_play import KitPlayState
from mars777_police.app.kit_records import KitRecordChain
from mars777_police.app.kit_sub_game import KitSubGame
from mars777_police.app.protocol_errors import StaleMessageError
from mars777_police.domain.terminal import Outcome
from mars777_police.protocol.secure_nonce import SecretsNonceSource

OURS = KitRole(ROLE.value)
THEIRS = KitRole.THIEF if OURS is KitRole.POLICE else KitRole.POLICE


def sub_game(sent: list[KitTurn], inbox: KitTurnInbox) -> KitSubGame:
    async def send(message: KitTurn) -> None:
        sent.append(message)

    return KitSubGame(
        maker=maker(KitRecordChain(CommitmentCodec.KIT_CORE_COMMITMENT_V1, SecretsNonceSource())),
        inbox=inbox,
        send=send,
        role=OURS,
        limits=limits_of(config()),
        deadline=5.0,
        state=KitPlayState.opening(config(), ROLE),
    )


def _terminal() -> object:
    from mars777_police.app.kit_adjudicate import KitVerdict

    return KitVerdict(Outcome.SURVIVAL, "settled for the test")


def _no_question() -> object:
    from mars777_police.app.capture_values import CaptureAnswer

    return CaptureAnswer.NO_QUESTION


def test_a_settled_sub_game_delivers_exactly_what_it_owes_and_no_more() -> None:
    """The pinned obligation, and its exact scope.

    A side that owes an **answer** must deliver it before it stops talking, or
    the opponent waits out its budget and settles a game it already lost as a
    timeout. A side that owes nothing sends nothing - a second terminal would be
    a duplicate, which is the other half of the same contract.
    """
    sent: list[KitTurn] = []
    inbox = KitTurnInbox()
    game = sub_game(sent, inbox)
    from mars777_police.app.capture_values import CaptureClaim

    if OURS is KitRole.THIEF:
        inbox.offer(peer_turn(1, capture_claim=CaptureClaim(game.state.truth.own_position)))
        outcome = asyncio.run(game.play())
        assert outcome is Outcome.CAPTURE
        # The thief moves first, so its own half-turn goes out before it ever sees
        # the claim; the terminal answer is the one that follows, and is the last.
        assert len(sent) == 2, "the answer we owed never rode out"
        assert sent[-1].claim_response is not None
        assert sent[-1].claim_response.caught is True
    else:
        inbox.offer(peer_turn(1, survival_claimed=True))
        outcome = asyncio.run(game.play())
        assert outcome is Outcome.SURVIVAL
        assert sent == [], "a side that owed nothing sent a terminal anyway"


def test_a_sub_game_settles_exactly_once() -> None:
    """One settlement per sub-game: a second would be a duplicate terminal."""
    sent: list[KitTurn] = []
    game = sub_game(sent, KitTurnInbox())
    verdict = game._verdict(None, _no_question())

    asyncio.run(game._settle(_terminal(), own=False))

    with pytest.raises(StaleMessageError):
        asyncio.run(game._settle(verdict, own=False))


def test_a_silent_opponent_is_refused_rather_than_scored() -> None:
    """A game that never happened is not a game we settle a score for."""
    sent: list[KitTurn] = []
    game = sub_game(sent, KitTurnInbox())
    game.deadline = 0.05

    with pytest.raises(StaleMessageError):
        asyncio.run(game.play())
