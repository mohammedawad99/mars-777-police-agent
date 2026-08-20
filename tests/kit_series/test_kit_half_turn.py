"""Our own half of a turn: decided, sealed, and announced in that order.

The decision comes from the strategy, the seal from the commitment codec, and
the announcement from neither - which is what stops a move being chosen after
the opponent's is known. The thief's survival claim rides the turn that reaches
the threshold rather than arriving afterwards.
"""

import asyncio

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
from mars777_police.domain.terminal import Outcome
from mars777_police.protocol.secure_nonce import SecretsNonceSource

OURS = KitRole(ROLE.value)


def _claim(game: KitSubGame) -> object:
    from mars777_police.app.capture_values import CaptureClaim

    return CaptureClaim(game.state.truth.own_position)


def _appender(sent: list[KitTurn]):
    async def send(message: KitTurn) -> None:
        sent.append(message)

    return send


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
