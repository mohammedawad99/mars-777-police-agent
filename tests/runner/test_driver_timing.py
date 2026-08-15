"""The three ordering rules, proved by the effects they prevent.

R1, R2 and R3 are not style. Each removes a way for one peer's same-step effect
to reach into the other's already-decided turn: R1 keeps the peer's step-`k`
barrier out of the board our emission is projected on, R2 keeps our own action
out of the cell we answer a capture question from, and R3 keeps the peer's
barrier out of the board our committed action is validated against.

JDEC-016 §4 is the authority for all three: `state.self_pos` and
`state.barriers` are **pre-action**, both actors of a step are checked against
that same start state, and the step's effects are applied only afterwards.
"""

import asyncio

import driver_builders as build
from driver_builders import board, facing

from mars777_police.app.capture_values import CaptureAnswer
from mars777_police.app.sealed_record_values import ActorRole
from mars777_police.domain.actions import MoveAction
from mars777_police.domain.board import Position
from mars777_police.domain.observation import Observation
from mars777_police.domain.rules import Move
from mars777_police.domain.scent_model_default import default_scent_model
from mars777_police.domain.scent_observation import emission_of
from mars777_police.domain.truth import LocalTruth

COP, THIEF = Position(0, 0), Position(0, 1)


class Fixed:
    """A strategy that always returns the one action it was built with."""

    def __init__(self, action: object, claim: object = None) -> None:
        self.action = action
        self.claim = claim

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


def _thief_at(cell: Position) -> object:
    """A live thief turn runtime standing on *cell*, ready for a reveal."""
    import turn_builders

    from mars777_police.app.turn_cursor import TurnCursor
    from mars777_police.domain.truth import LocalTruth

    live = turn_builders.runtime(ActorRole.THIEF)
    live.cursor = TurnCursor(1, 1)
    live.truth = LocalTruth(board=board(), own_position=cell)
    live.accept_commitment(turn_builders.commitment(live.cursor))
    live.acknowledge()
    return live


def _claimed(live: object, cell: Position) -> object:
    """The police's step-1 reveal, landing on *cell* and claiming it."""
    import turn_builders

    from mars777_police.app.capture_values import CaptureClaim
    from mars777_police.app.peer_turn_messages import Reveal

    reveal = Reveal(
        live.cursor,  # type: ignore[attr-defined]
        MoveAction(Move.S),
        "hint",
        CaptureClaim(cell),
        turn_builders.emission(),
    )
    return live.accept_reveal(reveal)  # type: ignore[attr-defined]


def test_r2_a_contact_claim_is_answered_from_the_pre_action_cell() -> None:
    live = _thief_at(Position(1, 1))
    assert _claimed(live, Position(1, 1)).capture is CaptureAnswer.CAUGHT  # type: ignore[attr-defined]
    other = _thief_at(Position(1, 1))
    assert _claimed(other, Position(1, 0)).capture is CaptureAnswer.NOT_CAUGHT  # type: ignore[attr-defined]


def test_r2_landing_on_the_same_cell_is_not_a_step_k_capture() -> None:
    live = _thief_at(Position(1, 1))
    answered = _claimed(live, Position(1, 0))
    assert answered.capture is CaptureAnswer.NOT_CAUGHT  # type: ignore[attr-defined]
    assert live.truth.own_position == Position(1, 1)  # type: ignore[attr-defined]


def test_r3_adoption_applies_our_action_against_the_round_start_board() -> None:
    """A peer barrier that appears on our destination cannot undo our commitment."""
    a, _ = facing(Fixed(MoveAction(Move.S)), Fixed(MoveAction(Move.S)))
    turn, start = a.context.current_turn(), a.driver.truth
    landing = Position(1, 0)
    turn.truth = LocalTruth(board=board(landing), own_position=start.own_position)
    adopted = a.driver.adopt(turn, MoveAction(Move.S), start)
    assert adopted.own_position == landing
    assert landing in adopted.board.blocked
    assert adopted.completed_steps == 1


def test_the_peers_same_step_barrier_survives_our_adoption() -> None:
    a, _ = facing(Fixed(MoveAction(Move.S)), Fixed(MoveAction(Move.S)))
    turn, start = a.context.current_turn(), a.driver.truth
    turn.truth = LocalTruth(board=board(Position(4, 4)), own_position=start.own_position)
    assert Position(4, 4) in a.driver.adopt(turn, MoveAction(Move.S), start).board.blocked


def test_the_scent_a_round_sent_is_the_one_its_own_action_produces() -> None:
    a, b = facing(Fixed(MoveAction(Move.S)), Fixed(MoveAction(Move.S)))
    police_turn, _ = _one_round(a, b)
    model = default_scent_model()
    assert _sent(police_turn) == emission_of(board(), model.kernel, Position(1, 0), model.params)
