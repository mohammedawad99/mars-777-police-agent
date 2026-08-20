"""Whose turn comes first, and what travels with it.

Lockstep is the whole contract: the thief moves first, a terminal answer rides
out on the turn that produced it rather than arriving as a later announcement,
and a schedule that gives this role three rows gets three rows played.
"""

import asyncio

from kit_backend_builders import backend
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

OURS = KitRole(ROLE.value)


def test_the_thief_moves_first_and_a_terminal_answer_rides_out() -> None:
    """`reference-v3` ordering and the terminal obligation, both role-neutral code."""
    from test_kit_play_loop import maker

    from mars777_police.app.kit_inbox import KitTurnInbox
    from mars777_police.app.kit_messages import KitTurn
    from mars777_police.app.kit_sub_game import KitSubGame
    from mars777_police.app.protocol_values import Sha256Digest

    sent: list[object] = []

    async def send(message: object) -> None:
        sent.append(message)

    chain = KitRecordChain(CommitmentCodec.KIT_CORE_COMMITMENT_V1, SecretsNonceSource())
    state = KitPlayState.opening(config(), ROLE)
    inbox = KitTurnInbox()
    game = KitSubGame(
        maker=maker(chain),
        inbox=inbox,
        send=send,
        role=KitRole.THIEF,
        limits=limits_of(config()),
        deadline=5.0,
        state=state,
    )

    async def run() -> Outcome:
        played = asyncio.ensure_future(game.play())
        for _ in range(500):
            if sent:
                break
            await asyncio.sleep(0.01)
        inbox.offer(
            KitTurn(
                1,
                KitRole.POLICE,
                "",
                (),
                Sha256Digest(COMMIT),
                "2026-08-18T00:00:00Z",
                capture_claim=CaptureClaim(game.state.truth.own_position),
            )
        )
        return await played

    outcome = asyncio.run(run())

    assert game.moves_first is True
    assert outcome is Outcome.CAPTURE
    assert sent[-1].claim_response is not None
    assert sent[-1].claim_response.caught is True


def test_a_backend_runs_every_row_the_schedule_gave_it() -> None:
    """Its own rows, in order, and never one the other backend owns."""
    played: list[int] = []

    class Counting(type(backend(KitRole.POLICE))):  # type: ignore[misc]
        async def play_sub_game(self, number: int) -> Outcome:
            self.require_ours(number)
            played.append(number)
            return Outcome.SURVIVAL

    template = backend(KitRole.POLICE)
    held = Counting(
        **{
            field.name: getattr(template, field.name)
            for field in __import__("dataclasses").fields(template)
        }
    )

    assert asyncio.run(held.run()) == dict.fromkeys(held.ours, Outcome.SURVIVAL)
    assert played == list(held.ours)


def test_our_own_turn_can_end_the_sub_game_and_the_claim_already_rode() -> None:
    """A survival our own move reached sends no terminal: the claim went with it."""
    from test_kit_play_loop import maker

    from mars777_police.app.kit_inbox import KitTurnInbox
    from mars777_police.app.kit_sub_game import KitSubGame

    sent: list[object] = []

    async def send(message: object) -> None:
        sent.append(message)

    limits = limits_of(config())
    chain = KitRecordChain(CommitmentCodec.KIT_CORE_COMMITMENT_V1, SecretsNonceSource())
    opening = KitPlayState.opening(config(), ROLE)
    game = KitSubGame(
        maker=maker(chain),
        inbox=KitTurnInbox(),
        send=send,
        role=KitRole.THIEF,
        limits=limits,
        deadline=5.0,
        state=KitPlayState(opening.truth, opening.field, limits.survival_threshold - 1),
    )

    outcome = asyncio.run(game.play())

    assert outcome is Outcome.SURVIVAL
    assert len(sent) == 1, "a terminal was duplicated, or the half-turn never went out"
    assert sent[0].survival_claimed is (OURS is KitRole.THIEF)
