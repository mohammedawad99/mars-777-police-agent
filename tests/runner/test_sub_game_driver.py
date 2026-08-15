"""One production driver, playing real lockstep rounds against a real peer.

Everything here is the shipped code except the wire: real `PeerRunner`, real
`TurnProtocolRuntime`, real `OutboundEvidenceRuntime` drawing real nonces, real
`LocalTurnService`. The driver is the thing under test, and what it is being
tested for is *when* it does each thing - the ordering rules are the contract.
"""

import asyncio

import driver_builders as build
from driver_builders import STARTS, facing

from mars777_police.app.sealed_record_values import ActorRole
from mars777_police.app.turn_protocol_state import TurnPhase
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


def test_one_round_uses_the_same_cursor_step_on_both_peers() -> None:
    a, b = _pair(Scripted(Move.S), Scripted(Move.S))
    played_a, played_b = a.context.current_turn(), b.context.current_turn()
    asyncio.run(_round(a, b))
    assert played_a.cursor.step == 1
    assert played_b.cursor.step == played_a.cursor.step
    assert a.producer.records[-1].cursor == b.producer.records[-1].cursor


def test_both_peers_enter_a_round_at_k_minus_one_and_leave_at_k() -> None:
    a, b = _pair(Scripted(Move.S), Scripted(Move.S))
    assert a.driver.truth.completed_steps == 0 and b.driver.truth.completed_steps == 0
    asyncio.run(_round(a, b))
    assert a.driver.truth.completed_steps == 1 and b.driver.truth.completed_steps == 1
    asyncio.run(_round(a, b))
    assert a.driver.truth.completed_steps == 2 and b.driver.truth.completed_steps == 2


def test_each_peer_increments_exactly_once_per_round() -> None:
    police, thief = Scripted(Move.S), Scripted(Move.S)
    a, b = _pair(police, thief)
    for expected in (1, 2, 3):
        asyncio.run(_round(a, b))
        assert a.driver.truth.completed_steps == expected
        assert len(police.seen) == expected


def test_the_strategy_is_asked_exactly_once_per_own_round() -> None:
    police, thief = Scripted(Move.S), Scripted(Move.S)
    a, b = _pair(police, thief)
    asyncio.run(_round(a, b))
    assert len(police.seen) == 1
    assert len(thief.seen) == 1


def test_the_observation_is_built_from_the_round_start_truth() -> None:
    police, thief = Scripted(Move.S), Scripted(Move.S)
    a, b = _pair(police, thief)
    asyncio.run(_round(a, b))
    assert police.seen[0].own_position == STARTS[ActorRole.POLICE]
    assert police.seen[0].board.blocked == frozenset()
    asyncio.run(_round(a, b))
    assert police.seen[1].own_position == a.driver.truth.own_position.__class__(1, 0)


def test_the_observation_still_has_exactly_three_fields() -> None:
    import dataclasses

    police, _ = Scripted(Move.S), Scripted(Move.S)
    a, b = _pair(police, Scripted(Move.S))
    asyncio.run(_round(a, b))
    assert tuple(f.name for f in dataclasses.fields(police.seen[0])) == (
        "board",
        "own_position",
        "quota",
    )


def test_a_round_leaves_both_tracks_complete_before_the_next_begins() -> None:
    a, b = _pair(Scripted(Move.S), Scripted(Move.S))
    played = [(side, side.context.current_turn()) for side in (a, b)]
    asyncio.run(_round(a, b))
    for side, turn in played:
        assert turn.phase is TurnPhase.CONSUMED
        assert turn.local_acknowledged is True
        assert side.driver.truth.completed_steps == turn.cursor.step
        assert side.context.current_turn().cursor.step == turn.cursor.step + 1


def test_the_action_the_strategy_chose_is_the_action_that_was_sealed() -> None:
    a, b = _pair(Scripted(Move.S), Scripted(Move.E))
    witness = b.context.current_turn()
    asyncio.run(_round(a, b))
    revealed = witness.evidence[-1].action
    assert revealed == MoveAction(Move.S)
    assert a.driver.truth.own_position == STARTS[ActorRole.POLICE].__class__(1, 0)
