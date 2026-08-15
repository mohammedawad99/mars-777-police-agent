"""The same-step barrier cases, which only a police-capable repository can play.

BAR-004 gives placement to the police alone, and `LocalTurnService` enforces that
by having no code path for it in the thief. So these scenarios - a barrier that
catches, one that misses, and one that lands on our own destination - are
exercised where a placement can actually be executed. The role-neutral halves of
the same contract live beside them in `test_driver_timing.py`.
"""

import asyncio

import driver_builders as build
from driver_builders import board, facing

from mars777_police.app.capture_values import CaptureAnswer
from mars777_police.app.sealed_record_values import ActorRole
from mars777_police.domain.actions import BarrierAction, MoveAction
from mars777_police.domain.board import Position
from mars777_police.domain.observation import Observation
from mars777_police.domain.rules import Move
from mars777_police.domain.scent_model_default import default_scent_model
from mars777_police.domain.scent_observation import emission_of

COP, THIEF = Position(0, 0), Position(0, 1)


class Fixed:
    """A strategy that always returns the one action it was built with."""

    def __init__(self, action: object) -> None:
        self.action = action

    def choose_action(self, observation: Observation) -> object:
        return self.action


async def _round(a: build.Peer, b: build.Peer) -> None:
    await asyncio.gather(a.driver.play_round(), b.driver.play_round())


def _one_round(a: build.Peer, b: build.Peer) -> tuple[object, object]:
    """Play round one and hand back the two runtimes that actually played it."""
    played = (a.context.current_turn(), b.context.current_turn())
    asyncio.run(_round(a, b))
    return played


def _sent(turn: object) -> object:
    return turn.capture.sent_scent[-1].emission  # type: ignore[attr-defined]


def _answered(turn: object) -> object:
    return turn.capture.inbound[-1].answer  # type: ignore[attr-defined]


def test_r1_our_emission_ignores_the_peers_same_step_barrier() -> None:
    a, b = facing(Fixed(BarrierAction(THIEF)), Fixed(MoveAction(Move.S)))
    _, thief_turn = _one_round(a, b)
    model = default_scent_model()
    expected = emission_of(board(), model.kernel, Position(1, 1), model.params)
    assert _sent(thief_turn) == expected


def test_r1_the_placer_emits_from_its_own_cell_on_its_own_new_board() -> None:
    a, b = facing(Fixed(BarrierAction(THIEF)), Fixed(MoveAction(Move.S)))
    police_turn, _ = _one_round(a, b)
    model = default_scent_model()
    assert _sent(police_turn) == emission_of(board(THIEF), model.kernel, COP, model.params)


def test_a_barrier_on_the_thiefs_pre_action_cell_catches_it_even_if_it_moves() -> None:
    a, b = facing(Fixed(BarrierAction(THIEF)), Fixed(MoveAction(Move.S)))
    _, thief_turn = _one_round(a, b)
    assert _answered(thief_turn) is CaptureAnswer.CAUGHT
    assert b.driver.captured is True
    assert a.driver.captured is True


def test_a_barrier_on_the_thiefs_destination_is_not_a_capture() -> None:
    a, b = facing(Fixed(BarrierAction(COP)), Fixed(MoveAction(Move.W)))
    _, thief_turn = _one_round(a, b)
    assert _answered(thief_turn) is CaptureAnswer.NO_QUESTION
    assert b.driver.captured is False


def test_r3_a_peer_barrier_on_our_destination_does_not_undo_our_committed_move() -> None:
    a, b = facing(Fixed(BarrierAction(COP)), Fixed(MoveAction(Move.W)))
    asyncio.run(_round(a, b))
    assert b.driver.truth.own_position == COP
    assert b.driver.truth.board.is_blocked(COP)
    assert b.driver.truth.completed_steps == 1


def test_the_peer_barrier_survives_our_own_adoption() -> None:
    a, b = facing(Fixed(BarrierAction(THIEF)), Fixed(MoveAction(Move.S)))
    asyncio.run(_round(a, b))
    assert THIEF in b.driver.truth.board.blocked
    assert b.driver.truth.own_position == Position(1, 1)


def test_both_validated_effects_are_kept_when_each_side_changes_the_board() -> None:
    a, b = facing(Fixed(BarrierAction(COP)), Fixed(MoveAction(Move.S)))
    asyncio.run(_round(a, b))
    assert a.driver.truth.board.blocked == frozenset({COP})
    assert b.driver.truth.board.blocked == frozenset({COP})
    assert a.driver.truth.own_position == COP
    assert b.driver.truth.own_position == Position(1, 1)


def test_the_step_start_board_is_what_the_sealed_state_reports() -> None:
    a, b = facing(Fixed(BarrierAction(THIEF)), Fixed(MoveAction(Move.S)))
    asyncio.run(_round(a, b))
    record = a.producer.records[-1]
    assert record.state.barriers == ()
    assert record.state.self_pos == COP
    assert record.state.role is ActorRole.POLICE
