"""A whole KIT sub-game played in process, against a scripted opponent.

The loop, the half-turn maker, the record chain and the adjudication are all
production; what a test supplies is the opponent's half of the wire. That is the
only honest way to pin the settlement contract, because the defect this exists
to prevent is invisible from either side alone: we settled `CAPTURE` and stopped
talking while the peer waited out its budget and settled `timeout`.
"""

import asyncio

import pytest
from kit_wire_vectors import COMMIT
from r16_builders import config

from mars777_police.__main__ import ROLE
from mars777_police.app.commitment_codecs import CommitmentCodec
from mars777_police.app.config_rules import hints_of, limits_of, rules_of
from mars777_police.app.kit_half_turn import KitHalfTurnMaker
from mars777_police.app.kit_inbox import KitTurnInbox
from mars777_police.app.kit_messages import KitRole, KitTurn
from mars777_police.app.kit_play import KitPlayState
from mars777_police.app.kit_records import KitRecordChain
from mars777_police.app.kit_sub_game import KitSubGame
from mars777_police.app.protocol_errors import StaleMessageError
from mars777_police.app.protocol_values import Sha256Digest
from mars777_police.app.turn_service import LocalTurnService
from mars777_police.domain.scent_model_default import default_scent_model
from mars777_police.domain.terminal import Outcome
from mars777_police.infra.clock import SystemClock
from mars777_police.protocol.secure_nonce import SecretsNonceSource

OURS = KitRole(ROLE.value)
THEIRS = KitRole.THIEF if OURS is KitRole.POLICE else KitRole.POLICE


def maker(chain: KitRecordChain) -> KitHalfTurnMaker:
    limits = limits_of(config())
    return KitHalfTurnMaker(
        role=OURS,
        actor=ROLE,
        sub_game=1,
        strategy=_Strategy(),
        turns=LocalTurnService(limits, rules_of(config()).quota),
        hints=hints_of(config(), ROLE),
        model=default_scent_model(),
        chain=chain,
        clock=SystemClock(),
        survival_threshold=limits.survival_threshold,
    )


class _Strategy:
    """`STAY`, which every role may always play - so the loop is what is tested."""

    def choose_action(self, observation: object) -> object:
        from mars777_police.domain.actions import MoveAction
        from mars777_police.domain.rules import Move

        return MoveAction(Move.STAY)


def peer_turn(step: int, **changes: object) -> KitTurn:
    fields: dict[str, object] = {
        "step": step,
        "sender": THEIRS,
        "hint": "over here",
        "smell_grid": (("0,0", 0.5),),
        "commit": Sha256Digest(COMMIT),
        "timestamp": "2026-08-18T00:00:00Z",
    }
    fields.update(changes)
    return KitTurn(**fields)  # type: ignore[arg-type]


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


def _terminal() -> object:
    from mars777_police.app.kit_adjudicate import KitVerdict

    return KitVerdict(Outcome.SURVIVAL, "settled for the test")


def _no_question() -> object:
    from mars777_police.app.capture_values import CaptureAnswer

    return CaptureAnswer.NO_QUESTION


def test_a_silent_opponent_is_refused_rather_than_scored() -> None:
    """A game that never happened is not a game we settle a score for."""
    sent: list[KitTurn] = []
    game = sub_game(sent, KitTurnInbox())
    game.deadline = 0.05

    with pytest.raises(StaleMessageError):
        asyncio.run(game.play())


def test_our_own_half_turn_is_decided_sealed_and_announced() -> None:
    """A neutral opponent turn draws a real half-turn out of us, sealed and sent."""
    sent: list[KitTurn] = []
    inbox = KitTurnInbox()
    chain = KitRecordChain(CommitmentCodec.KIT_CORE_COMMITMENT_V1, SecretsNonceSource())
    game = KitSubGame(
        maker=maker(chain),
        inbox=inbox,
        send=_appender(sent),
        role=OURS,
        limits=limits_of(config()),
        deadline=5.0,
        state=KitPlayState.opening(config(), ROLE),
    )
    inbox.offer(peer_turn(1))

    async def run() -> Outcome:
        played = asyncio.ensure_future(game.play())
        for _ in range(500):
            if sent:
                break
            await asyncio.sleep(0.01)
        inbox.offer(
            peer_turn(
                2,
                survival_claimed=OURS is KitRole.POLICE,
                capture_claim=_claim(game) if OURS is KitRole.THIEF else None,
            )
        )
        return await played

    outcome = asyncio.run(run())

    assert outcome in (Outcome.CAPTURE, Outcome.SURVIVAL)
    assert chain.records, "our own half-turn was never sealed"
    ours = sent[0]
    assert ours.sender is OURS
    assert ours.commit == chain.records[0].commit
    assert ours.timestamp
    assert dict(ours.smell_grid)
    if OURS is KitRole.POLICE:
        assert ours.capture_claim is not None
    else:
        assert ours.capture_claim is None


def test_the_thief_claims_survival_on_the_turn_that_reaches_the_threshold() -> None:
    """Claimed, never inferred: the cop cannot count the thief's steps for it."""
    chain = KitRecordChain(CommitmentCodec.KIT_CORE_COMMITMENT_V1, SecretsNonceSource())
    made = maker(chain)
    state = KitPlayState.opening(config(), ROLE)
    threshold = limits_of(config()).survival_threshold
    for _ in range(threshold - 1):
        state = made.take(state).state

    half = made.take(state)

    assert half.state.step == threshold
    assert half.message.survival_claimed is (OURS is KitRole.THIEF)


def _claim(game: KitSubGame) -> object:
    from mars777_police.app.capture_values import CaptureClaim

    return CaptureClaim(game.state.truth.own_position)


def _appender(sent: list[KitTurn]):
    async def send(message: KitTurn) -> None:
        sent.append(message)

    return send
