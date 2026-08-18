"""The privacy wall a strategy is allowed to see, and nothing beside it.

`Observation` is the only value a strategy receives, so what it *cannot* hold is
the load-bearing part of its contract: an opponent cell that never has a field
cannot leak through a code review that misses it. The field-set test below is
therefore written as an exact equality rather than a series of "does not have"
assertions - a new member fails it on arrival, which is the deliberate review
gate `PRD03-AC-001` asks for.
"""

import dataclasses

import pytest

from mars777_police.domain.barriers import BarrierQuota
from mars777_police.domain.board import Board, Position
from mars777_police.domain.observation import (
    InvalidObservationError,
    Observation,
    observation_of,
)
from mars777_police.domain.truth import LocalTruth

GRID = 7
QUOTA = BarrierQuota(14)
CENTRE = Position(3, 3)


def _board(*blocked: Position) -> Board:
    return Board(rows=GRID, cols=GRID, blocked=frozenset(blocked))


def _seen() -> Observation:
    return Observation(board=_board(), own_position=CENTRE, quota=QUOTA)


def test_the_field_set_is_exactly_what_a_decision_may_see() -> None:
    """Four members now, and the fourth is a belief rather than a truth.

    `scent` is what the opponent's own disclosed emissions imply about the
    environment; `ScentBelief` has no member an opponent cell could live in, so
    the rule this test has always enforced is unchanged - there is still no
    field an opponent position, a peer nonce or a reveal could arrive in.
    """
    assert tuple(f.name for f in dataclasses.fields(Observation)) == (
        "board",
        "own_position",
        "quota",
        "scent",
    )


def test_no_field_names_or_implies_opponent_truth() -> None:
    forbidden = ("opponent", "enemy", "peer", "thief", "police", "true", "replay", "audit")
    for field in dataclasses.fields(Observation):
        assert not any(word in field.name for word in forbidden)


def test_it_is_frozen() -> None:
    with pytest.raises(dataclasses.FrozenInstanceError):
        _seen().own_position = Position(0, 0)  # type: ignore[misc]


def test_it_is_slotted_so_no_field_can_be_attached_at_runtime() -> None:
    assert Observation.__slots__ == ("board", "own_position", "quota", "scent")
    assert not hasattr(_seen(), "__dict__")


def test_it_refuses_a_board_that_is_not_a_board() -> None:
    with pytest.raises(InvalidObservationError, match="board"):
        Observation(board=object(), own_position=CENTRE, quota=QUOTA)  # type: ignore[arg-type]


def test_it_refuses_a_position_that_is_not_a_position() -> None:
    with pytest.raises(InvalidObservationError, match="own_position"):
        Observation(board=_board(), own_position=(3, 3), quota=QUOTA)  # type: ignore[arg-type]


def test_it_refuses_a_quota_that_is_not_a_quota() -> None:
    with pytest.raises(InvalidObservationError, match="quota"):
        Observation(board=_board(), own_position=CENTRE, quota=14)  # type: ignore[arg-type]


def test_it_refuses_a_scent_that_is_not_a_belief() -> None:
    """The fourth member is typed like the other three, and for the same reason.

    A raw field or a bare number arriving where a belief belongs would let a
    policy read something nobody folded through the locked model.
    """
    with pytest.raises(InvalidObservationError, match="scent"):
        Observation(board=_board(), own_position=CENTRE, quota=QUOTA, scent=0.9)  # type: ignore[arg-type]


def test_it_refuses_a_position_that_is_not_on_its_own_board() -> None:
    with pytest.raises(InvalidObservationError, match="outside"):
        Observation(board=_board(), own_position=Position(9, 9), quota=QUOTA)


def test_a_blocked_own_cell_is_allowed_because_bar_004_permits_standing_on_one() -> None:
    observation = Observation(board=_board(CENTRE), own_position=CENTRE, quota=QUOTA)
    assert observation.board.is_blocked(observation.own_position)


def test_the_builder_projects_local_truth_without_copying_its_step_count() -> None:
    truth = LocalTruth(board=_board(), own_position=CENTRE, completed_steps=9)
    observation = observation_of(truth, QUOTA)
    assert observation.board is truth.board
    assert observation.own_position is truth.own_position
    assert observation.quota is QUOTA
    assert not hasattr(observation, "completed_steps")


def test_the_builder_leaves_the_truth_it_read_untouched() -> None:
    truth = LocalTruth(board=_board(), own_position=CENTRE, completed_steps=2)
    observation_of(truth, QUOTA)
    assert truth == LocalTruth(board=_board(), own_position=CENTRE, completed_steps=2)
