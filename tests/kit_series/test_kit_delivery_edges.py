"""Turns held back and released together, and the order they are applied in.

A batch that arrives at once is still applied turn by turn: the delivery
contract buffers, it never reorders, and a sub-game that needs a second round
gets one without either side inventing a state the other has not reached.
"""

import asyncio

import pytest
from kit_backend_builders import drop
from kit_wire_vectors import COMMIT
from r16_builders import config

from mars777_police.__main__ import ROLE
from mars777_police.app.capture_values import CaptureClaim
from mars777_police.app.commitment_codecs import CommitmentCodec
from mars777_police.app.config_rules import limits_of
from mars777_police.app.kit_messages import KitRole
from mars777_police.app.kit_play import KitPlayState
from mars777_police.app.kit_records import KitRecordChain
from mars777_police.domain.terminal import Outcome
from mars777_police.protocol.secure_nonce import SecretsNonceSource


@pytest.mark.parametrize("role", [KitRole.POLICE, KitRole.THIEF])
def test_a_sub_game_that_needs_two_rounds_takes_two_rounds(role: KitRole) -> None:
    """The loop is a loop, and both orderings come back for another round.

    Parameterised over the role because the ordering branch is role-neutral code:
    the thief opens each sub-game and the cop answers, whichever side we are.
    """
    from test_kit_play_loop import maker

    from mars777_police.app.kit_inbox import KitTurnInbox
    from mars777_police.app.kit_messages import KitTurn
    from mars777_police.app.kit_sub_game import KitSubGame
    from mars777_police.app.protocol_values import Sha256Digest

    sent: list[object] = []

    async def send(message: object) -> None:
        sent.append(message)

    chain = KitRecordChain(CommitmentCodec.KIT_CORE_COMMITMENT_V1, SecretsNonceSource())
    inbox = KitTurnInbox()
    game = KitSubGame(
        maker=maker(chain),
        inbox=inbox,
        send=send,
        role=role,
        limits=limits_of(config()),
        deadline=5.0,
        state=KitPlayState.opening(config(), ROLE),
    )
    opener = KitRole.THIEF if role is KitRole.POLICE else KitRole.POLICE

    def neutral(step: int, **changes: object) -> KitTurn:
        fields: dict[str, object] = {
            "step": step,
            "sender": opener,
            "hint": "",
            "smell_grid": (),
            "commit": Sha256Digest(COMMIT),
            "timestamp": "2026-08-18T00:00:00Z",
        }
        fields.update(changes)
        return KitTurn(**fields)  # type: ignore[arg-type]

    async def run() -> Outcome:
        played = asyncio.ensure_future(game.play())
        inbox.offer(neutral(1))
        # Wait until our own half-turn has actually gone out, so the second
        # opponent turn lands on a round we really played rather than on the first.
        for _ in range(500):
            if sent:
                break
            await asyncio.sleep(0.01)
        # The terminal each side can actually be told: a cop claims our cell, a
        # thief claims the threshold. Neither invents the other's ending.
        ending: dict[str, object] = (
            {"capture_claim": CaptureClaim(game.state.truth.own_position)}
            if opener is KitRole.POLICE
            else {"survival_claimed": True}
        )
        inbox.offer(neutral(2, **ending))
        return await played

    outcome = asyncio.run(run())

    assert outcome in (Outcome.CAPTURE, Outcome.SURVIVAL)
    assert len(chain.records) >= 1, "our own half-turn was never sealed"


def test_two_turns_released_together_are_both_applied_in_step_order() -> None:
    """A buffered arrival and the turn that unblocks it reach the loop as one batch."""
    from mars777_police.app.kit_inbox import KitTurnInbox
    from mars777_police.app.kit_messages import KitTurn
    from mars777_police.app.protocol_values import Sha256Digest

    inbox = KitTurnInbox()

    def turn(step: int) -> KitTurn:
        return KitTurn(
            step,
            KitRole.POLICE,
            "",
            (),
            Sha256Digest(COMMIT),
            "2026-08-18T00:00:00Z",
        )

    assert inbox.offer(turn(2)) == ()
    applied = inbox.offer(turn(1))

    assert [one.step for one in applied] == [1, 2]


def test_a_released_batch_is_applied_turn_by_turn_by_the_loop() -> None:
    """Both turns reach the game, in step order, from one wake-up."""
    from test_kit_play_loop import maker

    from mars777_police.app.kit_inbox import KitTurnInbox
    from mars777_police.app.kit_messages import KitTurn
    from mars777_police.app.kit_sub_game import KitSubGame
    from mars777_police.app.protocol_values import Sha256Digest

    inbox = KitTurnInbox()
    chain = KitRecordChain(CommitmentCodec.KIT_CORE_COMMITMENT_V1, SecretsNonceSource())
    game = KitSubGame(
        maker=maker(chain),
        inbox=inbox,
        send=drop,
        role=KitRole.THIEF,
        limits=limits_of(config()),
        deadline=5.0,
        state=KitPlayState.opening(config(), ROLE),
    )

    def turn(step: int) -> KitTurn:
        return KitTurn(step, KitRole.POLICE, "", (), Sha256Digest(COMMIT), "2026-08-18T00:00:00Z")

    inbox.offer(turn(2))
    inbox.offer(turn(1))

    verdict = asyncio.run(game._consume())

    assert verdict.outcome is None
    assert game.steps_seen == 2
