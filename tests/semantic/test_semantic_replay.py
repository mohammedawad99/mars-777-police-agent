"""Reconstructing both trajectories from the two disclosed logs.

Every board fact below comes from the locked config, and every legality verdict
from `domain.rules` / `domain.barriers` - the replay adds ordering, not rules.
"""

import pytest
from semantic_builders import COP, NORTH, RULES, THIEF

from mars777_police.app.sealed_record_values import ActorRole
from mars777_police.app.semantic_replay import PlayedTurn, Replay
from mars777_police.app.semantic_values import SemanticVerdict
from mars777_police.domain.actions import BarrierAction, MoveAction
from mars777_police.domain.board import Position
from mars777_police.domain.rules import Move

POLICE, THIEF_ROLE = ActorRole.POLICE, ActorRole.THIEF
SOUTH, EAST = MoveAction(Move.S), MoveAction(Move.E)


def turn(
    step: int,
    role: ActorRole,
    cell: Position,
    action: object,
    barriers: tuple[Position, ...] = (),
) -> PlayedTurn:
    """One disclosed turn, as either side's log would carry it."""
    return PlayedTurn(step, role, cell, barriers, action)  # type: ignore[arg-type]


def replay() -> Replay:
    """A fresh replay of the locked opening position."""
    return Replay(RULES)


def test_both_sides_open_on_the_cells_the_config_locked() -> None:
    live = replay()
    assert live.cell_of(POLICE) == COP
    assert live.cell_of(THIEF_ROLE) == THIEF
    assert live.check((turn(1, POLICE, COP, SOUTH), turn(1, THIEF_ROLE, THIEF, NORTH))).consistent


def test_a_legal_step_moves_both_pieces_exactly_where_the_moves_lead() -> None:
    live = replay()
    played = (turn(1, POLICE, COP, SOUTH), turn(1, THIEF_ROLE, THIEF, NORTH))
    live.apply(played)
    assert live.cell_of(POLICE) == Position(COP.row + 1, COP.col)
    assert live.cell_of(THIEF_ROLE) == Position(THIEF.row - 1, THIEF.col)


def test_a_side_that_opens_somewhere_else_is_caught_at_its_first_turn() -> None:
    finding = replay().check((turn(1, THIEF_ROLE, Position(6, 6), NORTH),))
    assert finding.verdict is SemanticVerdict.WRONG_START
    assert (finding.step, finding.at_fault) == (1, THIEF_ROLE)
    assert not finding.honest


def test_a_piece_that_teleports_between_its_own_turns_breaks_the_trajectory() -> None:
    live = replay()
    live.apply((turn(1, THIEF_ROLE, THIEF, NORTH),))
    finding = live.check((turn(2, THIEF_ROLE, Position(6, 6), NORTH),))
    assert finding.verdict is SemanticVerdict.BROKEN_TRAJECTORY
    assert finding.at_fault is THIEF_ROLE


def test_a_move_off_the_board_is_illegal() -> None:
    """The police starts in the corner, so north leaves the grid entirely."""
    finding = replay().check((turn(1, POLICE, COP, NORTH),))
    assert finding.verdict is SemanticVerdict.ILLEGAL_ACTION
    assert (finding.step, finding.at_fault) == (1, POLICE)


def test_a_move_into_a_barrier_placed_earlier_is_illegal() -> None:
    live = replay()
    live.apply((turn(1, POLICE, COP, BarrierAction(Position(1, 0))),))
    finding = live.check((turn(2, POLICE, COP, SOUTH, (Position(1, 0),)),))
    assert finding.verdict is SemanticVerdict.ILLEGAL_ACTION


def test_a_barrier_beyond_the_placer_s_reach_is_illegal() -> None:
    finding = replay().check((turn(1, POLICE, COP, BarrierAction(Position(4, 4))),))
    assert finding.verdict is SemanticVerdict.ILLEGAL_ACTION


def test_a_thief_that_discloses_a_barrier_is_refused_by_bar_004() -> None:
    """Placement is the police's alone, and only a replay knows which side is."""
    finding = replay().check((turn(1, THIEF_ROLE, THIEF, BarrierAction(Position(3, 4))),))
    assert finding.verdict is SemanticVerdict.ILLEGAL_ACTION
    assert finding.at_fault is THIEF_ROLE


def test_a_snapshot_carrying_a_barrier_nobody_placed_is_refused() -> None:
    finding = replay().check((turn(1, POLICE, COP, SOUTH, (Position(2, 2),)),))
    assert finding.verdict is SemanticVerdict.WRONG_BARRIER_SET
    assert (finding.step, finding.at_fault) == (1, POLICE)


def test_a_snapshot_that_omits_a_barrier_that_was_placed_is_refused() -> None:
    live = replay()
    live.apply((turn(1, POLICE, COP, BarrierAction(Position(0, 1))),))
    finding = live.check((turn(2, THIEF_ROLE, THIEF, NORTH),))
    assert finding.verdict is SemanticVerdict.WRONG_BARRIER_SET
    assert finding.at_fault is THIEF_ROLE


def test_a_barrier_placed_this_step_is_in_no_snapshot_of_this_step() -> None:
    """Both commitments for a step are sealed before either reveal opens."""
    live, target = replay(), Position(0, 1)
    played = (turn(1, POLICE, COP, BarrierAction(target)), turn(1, THIEF_ROLE, THIEF, NORTH))
    assert live.check(played).consistent
    live.apply(played)
    assert live.board.is_blocked(target)
    assert not RULES.board.is_blocked(target)


@pytest.mark.parametrize("role", [POLICE, THIEF_ROLE])
def test_the_start_cell_a_replay_uses_is_the_one_the_config_locked(role: ActorRole) -> None:
    assert RULES.start_for(role) == (COP if role is POLICE else THIEF)
