"""Reading one finished round into the truth the next one starts from.

Pure functions over values other owners already validated, so they are tested
here directly rather than through a protocol exchange: the union that keeps both
sides' placements is the part a live test would only ever exercise by accident,
and it is exactly the part that must never silently drop one.
"""

import turn_builders

from mars777_police.app.capture_values import CaptureAnswer, CaptureClaim, TurnOutcome
from mars777_police.app.peer_turn_messages import Reveal
from mars777_police.app.sealed_record_values import ActorRole
from mars777_police.app.sub_game_truth import caught_in, declared_barriers, merged_truth
from mars777_police.app.turn_cursor import TurnCursor
from mars777_police.domain.actions import MoveAction
from mars777_police.domain.board import Board, Position
from mars777_police.domain.rules import Move
from mars777_police.domain.truth import LocalTruth

GRID = 7
OURS, THEIRS = Position(1, 1), Position(4, 4)


def _board(*blocked: Position) -> Board:
    return Board(rows=GRID, cols=GRID, blocked=frozenset(blocked))


def _truth(cell: Position, *blocked: Position, steps: int = 0) -> LocalTruth:
    return LocalTruth(board=_board(*blocked), own_position=cell, completed_steps=steps)


def test_declared_barriers_is_sorted_and_not_a_set() -> None:
    truth = _truth(OURS, Position(3, 1), Position(0, 2), Position(3, 0))
    assert declared_barriers(truth) == (Position(0, 2), Position(3, 0), Position(3, 1))


def test_declared_barriers_of_an_empty_board_is_empty() -> None:
    assert declared_barriers(_truth(OURS)) == ()


def test_declared_barriers_ignores_the_order_the_set_was_built_in() -> None:
    cells = (Position(2, 2), Position(0, 5), Position(6, 1))
    first = declared_barriers(_truth(OURS, *cells))
    for rotation in range(len(cells)):
        shuffled = cells[rotation:] + cells[:rotation]
        assert declared_barriers(_truth(OURS, *shuffled)) == first


def test_the_merge_keeps_our_position_and_our_step_count() -> None:
    pending = _truth(Position(2, 1), steps=4)
    live = _truth(OURS, THEIRS)
    merged = merged_truth(pending, live)
    assert merged.own_position == Position(2, 1)
    assert merged.completed_steps == 4


def test_the_merge_keeps_both_sides_placements() -> None:
    pending = _truth(OURS, Position(1, 2), steps=1)
    live = _truth(OURS, THEIRS)
    assert merged_truth(pending, live).board.blocked == frozenset({Position(1, 2), THEIRS})


def test_the_merge_never_loses_the_peers_barrier_when_we_only_moved() -> None:
    pending = _truth(Position(2, 1), steps=1)
    live = _truth(OURS, THEIRS)
    assert merged_truth(pending, live).board.blocked == frozenset({THEIRS})


def test_the_merge_never_loses_our_barrier_when_the_peer_only_moved() -> None:
    pending = _truth(OURS, Position(1, 2), steps=1)
    live = _truth(OURS)
    assert merged_truth(pending, live).board.blocked == frozenset({Position(1, 2)})


def test_the_merge_keeps_the_geometry_it_was_given() -> None:
    merged = merged_truth(_truth(OURS, steps=1), _truth(OURS))
    assert (merged.board.rows, merged.board.cols, merged.board.start_index) == (GRID, GRID, 0)


def test_a_turn_nobody_asked_about_reports_no_capture() -> None:
    assert caught_in(turn_builders.runtime(ActorRole.POLICE)) is False


def _reveal(cell: Position) -> Reveal:
    """A move reveal that declares *cell*, exactly as the police would."""
    return Reveal(
        TurnCursor(1, 1),
        MoveAction(Move.N),
        "hint",
        CaptureClaim(cell),
        turn_builders.emission(),
    )


def test_a_yes_in_either_direction_is_a_capture() -> None:
    for direction in ("inbound", "outgoing"):
        live = turn_builders.runtime(ActorRole.POLICE)
        record = getattr(live.capture, f"observe_{direction}")
        record(_reveal(Position(3, 3)), TurnOutcome(True, CaptureAnswer.CAUGHT))
        assert caught_in(live) is True


def test_a_no_in_both_directions_is_not_a_capture() -> None:
    live = turn_builders.runtime(ActorRole.POLICE)
    live.capture.observe_inbound(
        _reveal(Position(0, 0)), TurnOutcome(True, CaptureAnswer.NOT_CAUGHT)
    )
    live.capture.observe_outgoing(
        _reveal(Position(0, 0)), TurnOutcome(True, CaptureAnswer.NO_QUESTION)
    )
    assert caught_in(live) is False


def test_the_claim_that_travelled_is_the_one_retained() -> None:
    live = turn_builders.runtime(ActorRole.POLICE)
    live.capture.observe_inbound(
        _reveal(Position(3, 3)), TurnOutcome(True, CaptureAnswer.NOT_CAUGHT)
    )
    assert live.capture.inbound[-1].claim == CaptureClaim(Position(3, 3))
