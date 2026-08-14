"""Where this turn's scent comes from, and what projecting it must never touch.

The emission belongs to the cell the actor stands on **after** its action, so it
cannot be known until the action has been applied - and applying it is exactly
what the sender must not really do, because no owner has yet learned whether the
peer accepted the turn. `ScentTurnProjector` resolves that by previewing through
the real `LocalTurnService` and handing the authoritative truth back untouched.

Nothing here fakes physics: the service is the role's own, the model is the
agreed one, and the deposits come from `emission_of`.
"""

import dataclasses

import pytest
import turn_builders as build

from mars777_police.app.scent_turn_projection import ScentTurnProjector, emission_for
from mars777_police.app.turn_service import InvalidActionError
from mars777_police.domain.actions import BarrierAction, MoveAction
from mars777_police.domain.board import Position
from mars777_police.domain.rules import Move, apply_move
from mars777_police.domain.scent_model_default import default_scent_model
from mars777_police.domain.scent_observation import emission_of
from mars777_police.domain.truth import LocalTruth

MODEL = default_scent_model()


def projector() -> ScentTurnProjector:
    """The production projector over this role's real service and model."""
    return ScentTurnProjector(build.service(), MODEL)


def expected_at(cell: Position) -> object:
    """What the agreed model deposits around *cell* on this board."""
    return emission_of(build.board(), MODEL.kernel, cell, MODEL.params)


def test_a_move_emits_from_the_cell_the_move_reaches() -> None:
    """Post-action, never pre-action: north first, then the deposits."""
    truth = build.truth()
    after = apply_move(truth.board, truth.own_position, Move.N)
    assert after != truth.own_position
    assert projector().project(truth, MoveAction(Move.N)) == expected_at(after)


def test_staying_still_emits_from_the_unchanged_cell() -> None:
    truth = build.truth()
    emission = projector().project(truth, MoveAction(Move.STAY))
    assert emission == expected_at(truth.own_position)
    assert emission.deposits, "a stationary agent still leaves scent"


def test_a_barrier_emits_from_the_cell_the_actor_never_left() -> None:
    """Placement is not movement: the centre is where the police already stood."""
    truth = build.truth()
    target = Position(truth.own_position.row, truth.own_position.col + 1)
    assert projector().project(truth, BarrierAction(target)) == expected_at(truth.own_position)


def test_an_illegal_move_produces_no_emission_at_all() -> None:
    with pytest.raises(InvalidActionError, match="rejected move"):
        projector().project(build.truth(), MoveAction(Move.S))


def test_an_illegal_placement_produces_no_emission_at_all() -> None:
    far = Position(build.CENTRE.row + 3, build.CENTRE.col + 3)
    with pytest.raises(InvalidActionError, match="rejected barrier"):
        projector().project(build.truth(), BarrierAction(far))


def test_projection_leaves_the_authoritative_truth_exactly_as_it_was() -> None:
    """A preview, not a turn: nothing has been played until the peer answers."""
    truth = build.truth()
    before = dataclasses.astuple(truth)
    projector().project(truth, MoveAction(Move.N))
    assert dataclasses.astuple(truth) == before
    assert truth.own_position == build.CENTRE and truth.completed_steps == 0


def test_the_helper_projects_for_the_role_whose_runtime_it_is_given() -> None:
    runtime = build.runtime()
    emission = emission_for(runtime, MODEL, MoveAction(Move.N))
    after = apply_move(runtime.truth.board, runtime.truth.own_position, Move.N)
    assert emission == expected_at(after)
    assert runtime.truth == build.truth(), "the runtime's truth is untouched"


def test_two_different_actions_emit_from_two_different_cells() -> None:
    """The emission follows the action, so it cannot be reused across actions."""
    truth = build.truth()
    north = projector().project(truth, MoveAction(Move.N))
    east = projector().project(truth, MoveAction(Move.E))
    assert north != east


def test_the_projector_holds_no_truth_of_its_own() -> None:
    members = {field.name for field in dataclasses.fields(ScentTurnProjector)}
    assert members == {"turns", "model"}, "a service and a model, never a position"


def test_a_board_edge_clips_through_the_domain_and_nothing_else() -> None:
    """No wrap-around, and no clipping rule written a second time here."""
    corner = LocalTruth(board=build.board(), own_position=Position(0, 0))
    emission = projector().project(corner, MoveAction(Move.STAY))
    assert emission == expected_at(Position(0, 0))
    assert all(one.cell.row >= 0 and one.cell.col >= 0 for one in emission.deposits)
    assert len(emission.deposits) < 25, "a corner emits fewer cells than the full window"
