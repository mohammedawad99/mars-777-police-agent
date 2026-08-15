"""When our own action becomes authoritative, and the four times it must not.

Adoption is the one place the driver writes game state, so every path that could
write it twice, write it early or write it after a failure is exercised here.
The guard is derived rather than flagged: `completed_steps` and `cursor.step`
already say whether this round was adopted, so no boolean records it.
"""

import asyncio

import driver_builders as build
import pytest
from driver_builders import LIMITS, STARTS, facing

from mars777_police.app.protocol_errors import LocalDefectError
from mars777_police.app.sealed_record_values import ActorRole
from mars777_police.app.turn_protocol_state import TurnPhase
from mars777_police.app.turn_service import InvalidActionError
from mars777_police.domain.actions import MoveAction
from mars777_police.domain.observation import Observation
from mars777_police.domain.rules import Move
from mars777_police.domain.terminal import Outcome


class Scripted:
    """A strategy that records every observation it was shown."""

    def __init__(self, *moves: Move) -> None:
        self.moves = list(moves)
        self.seen: list[Observation] = []

    def choose_action(self, observation: Observation) -> MoveAction:
        self.seen.append(observation)
        return MoveAction(self.moves[(len(self.seen) - 1) % len(self.moves)])


async def _round(a: build.Peer, b: build.Peer) -> None:
    await asyncio.gather(a.driver.play_round(), b.driver.play_round())


async def _series(a: build.Peer, b: build.Peer) -> list[Outcome]:
    return list(await asyncio.gather(a.driver.play_sub_game(), b.driver.play_sub_game()))


def _pair(police: Scripted, thief: Scripted) -> tuple[build.Peer, build.Peer]:
    return facing(police, thief)


def test_a_second_adoption_for_one_cursor_is_a_local_defect() -> None:
    a, b = _pair(Scripted(Move.S), Scripted(Move.S))
    played = a.context.current_turn()
    asyncio.run(_round(a, b))
    before = a.driver.truth
    with pytest.raises(LocalDefectError, match="already"):
        a.driver.adopt(played, MoveAction(Move.S), before)
    assert a.driver.truth is before
    assert a.driver.truth.completed_steps == 1


def test_an_illegal_choice_never_reaches_the_peer_and_never_adopts() -> None:
    a, _ = _pair(Scripted(Move.N), Scripted(Move.S))
    with pytest.raises(InvalidActionError, match="rejected move"):
        asyncio.run(a.driver.play_round())
    assert a.driver.truth.completed_steps == 0
    assert a.driver.truth.own_position == STARTS[ActorRole.POLICE]


def test_the_driver_derives_survival_at_the_locked_threshold() -> None:
    a, b = _pair(Scripted(Move.S, Move.N), Scripted(Move.S, Move.N))
    outcomes = asyncio.run(_series(a, b))
    assert outcomes == [Outcome.SURVIVAL, Outcome.SURVIVAL]
    assert a.driver.truth.completed_steps == LIMITS.survival_threshold
    assert b.driver.truth.completed_steps == LIMITS.survival_threshold


def test_the_strategy_is_asked_once_per_round_and_never_after_the_terminal() -> None:
    police, thief = Scripted(Move.S, Move.N), Scripted(Move.S, Move.N)
    a, b = _pair(police, thief)
    asyncio.run(_series(a, b))
    assert len(police.seen) == LIMITS.survival_threshold
    assert len(thief.seen) == LIMITS.survival_threshold


def test_a_refused_action_is_not_adopted() -> None:
    a, b = _pair(Scripted(Move.S), Scripted(Move.S))
    a.loopback.reject = True
    with pytest.raises(LocalDefectError, match="could not accept"):
        asyncio.run(_round(a, b))
    assert a.driver.truth.completed_steps == 0
    assert a.driver.truth.own_position == STARTS[ActorRole.POLICE]


def test_no_round_after_the_terminal_is_ever_bound() -> None:
    """Survival ends the sub-game; nothing may prepare a step the game never has."""
    police, thief = Scripted(Move.S, Move.N), Scripted(Move.S, Move.N)
    a, b = _pair(police, thief)
    outcomes = asyncio.run(_series(a, b))
    assert outcomes == [Outcome.SURVIVAL, Outcome.SURVIVAL]
    for side, chooser in ((a, police), (b, thief)):
        assert side.driver.truth.completed_steps == LIMITS.survival_threshold
        assert side.context.current_turn().cursor.step == LIMITS.survival_threshold
        assert len(chooser.seen) == LIMITS.survival_threshold


def test_the_terminal_round_leaves_no_unused_evidence_runtime() -> None:
    a, b = _pair(Scripted(Move.S, Move.N), Scripted(Move.S, Move.N))
    asyncio.run(_series(a, b))
    for side in (a, b):
        assert side.context.current_turn().phase is TurnPhase.CONSUMED
        assert len(side.producer.records) == LIMITS.survival_threshold
