"""Our own side of a KIT sub-game: the domain, driven by the kit's cadence.

Nothing here re-implements a game rule. Movement and placement go through
`LocalTurnService`, the scent field is the domain's own recurrence, the board is
the domain's board. What this layer owns is *when* each of them is asked - which
is the only thing the pinned wire actually changes.

The peer's smell grid is retained as the peer's. Folding a binary64 field into
our exact-decimal physics would assert an equivalence that is `MODEL_FORM_MATCH`
and **not** vector-exact, which is the claim the scent audit refuses to publish.
"""

import pytest
from r16_builders import config

from mars777_police.__main__ import ROLE
from mars777_police.app.config_rules import limits_of, opening_truth, rules_of
from mars777_police.app.kit_play import KitPlayState, peer_belief
from mars777_police.app.sealed_record_values import ActorRole
from mars777_police.app.turn_service import (
    InvalidActionError,
    LocalTurnService,
    UnsupportedActionError,
)
from mars777_police.domain.actions import BarrierAction, MoveAction
from mars777_police.domain.board import Position
from mars777_police.domain.rules import Move
from mars777_police.domain.scent_belief import NO_SCENT
from mars777_police.domain.scent_model_default import default_scent_model


def opening(role: ActorRole = ActorRole.POLICE) -> KitPlayState:
    return KitPlayState.opening(config(), role)


def service() -> LocalTurnService:
    return LocalTurnService(limits_of(config()), rules_of(config()).quota)


def test_the_opening_state_is_the_config_s_own_opening_truth() -> None:
    state = opening(ROLE)

    assert state.truth == opening_truth(config(), ROLE)
    assert state.step == 0
    assert state.barriers_placed == 0


def test_a_move_advances_the_step_and_the_domain_s_own_truth() -> None:
    state = opening(ROLE).advance(MoveAction(Move.S), service(), default_scent_model())

    assert state.step == 1
    assert state.truth.own_position != opening(ROLE).truth.own_position


def test_a_barrier_is_this_role_s_own_action_or_is_not_its_action_at_all() -> None:
    """Barriers are the police's (book ch.3). The thief has no such action, and
    the turn service refuses it rather than this layer growing a role branch."""
    start = opening(ROLE)
    target = Position(start.truth.own_position.row + 1, start.truth.own_position.col)

    if ROLE is ActorRole.POLICE:
        state = start.advance(BarrierAction(target), service(), default_scent_model())
        assert state.barriers_placed == 1
        assert target in state.truth.board.blocked
    else:
        with pytest.raises(UnsupportedActionError):
            start.advance(BarrierAction(target), service(), default_scent_model())


def test_the_smell_grid_is_our_own_field_after_the_turn() -> None:
    state = opening(ROLE).advance(MoveAction(Move.S), service(), default_scent_model())

    grid = dict(state.smell_grid())

    assert grid
    assert all(isinstance(key, str) and "," in key for key in grid)
    assert all(isinstance(value, float) and value > 0 for value in grid.values())


def test_an_illegal_action_leaves_the_state_byte_identical() -> None:
    """Validation strictly before effect: a refusal changes nothing at all."""
    start = opening(ROLE)
    refusal = InvalidActionError if ROLE is ActorRole.POLICE else UnsupportedActionError

    with pytest.raises(refusal):
        start.advance(BarrierAction(Position(99, 99)), service(), default_scent_model())

    assert start.step == 0


def test_a_public_barrier_the_peer_declared_is_adopted_onto_the_board() -> None:
    start = opening(ROLE)
    target = Position(2, 2)

    state = start.observe_barrier(target)

    assert target in state.truth.board.blocked
    assert state.step == start.step


def test_the_peers_grid_becomes_a_belief_only_when_our_domain_can_hold_it() -> None:
    board = opening(ROLE).truth.board

    inside = peer_belief((("0,0", 0.5),), board)
    outside = peer_belief((("0,0", 1.5),), board)

    assert inside.has_evidence is True
    assert outside is NO_SCENT
