"""What the live window may know, proved against the value a decision uses.

`GUI-001` permits own position, sensed scent, received hints and a belief map;
`GUI-002` forbids the objective board state. These tests hold the projection to
`Observation`, which is the strategy's own whitelist - so the window can never
be shown a fact the agent does not already lawfully hold.
"""

from dataclasses import fields

import gui_fixtures as fix

from mars777_police.app.live_view_values import LiveViewSnapshot, belief_cells, snapshot_of
from mars777_police.domain.observation import Observation


def test_the_snapshot_carries_no_field_an_opponent_cell_could_arrive_in() -> None:
    named = {one.name for one in fields(LiveViewSnapshot)}
    forbidden = {
        "opponent",
        "opponent_cell",
        "peer_position",
        "police",
        "police_cell",
        "thief",
        "thief_cell",
    }
    """Both roles, in both repositories: a live view may name neither side's cell."""
    assert named & forbidden == set()


def test_the_projection_reads_only_the_observation_it_was_given() -> None:
    view = fix.observation()
    snapshot = snapshot_of(view, role="POLICE", game_id="g", sub_game=1, step=1, phase="TURN")
    assert snapshot.own_cell == (view.own_position.row, view.own_position.col)
    assert snapshot.barriers == tuple(sorted((one.row, one.col) for one in view.board.blocked))
    assert snapshot.grid_size == view.board.rows
    assert snapshot.barrier_quota == view.quota.max_barriers


def test_a_silent_sub_game_publishes_no_belief_at_all() -> None:
    assert belief_cells(fix.observation()) == ()
    assert fix.snapshot().has_belief is False


def test_belief_is_published_as_the_decimal_text_the_agent_actually_held() -> None:
    cells = belief_cells(fix.observation(fix.belief((3, 3, "0.9"), (4, 1, "0.25"))))
    assert cells == ((3, 3, "0.9"), (4, 1, "0.25"))
    assert all(isinstance(value, str) for _, _, value in cells)


def test_a_zero_cell_is_not_evidence_and_is_not_drawn() -> None:
    cells = belief_cells(fix.observation(fix.belief((3, 3, "0.5"), (4, 4, "0"))))
    assert [(row, col) for row, col, _ in cells] == [(3, 3)]


def test_the_observation_itself_still_has_nowhere_to_put_an_opponent() -> None:
    assert {one.name for one in fields(Observation)} == {
        "board",
        "own_position",
        "quota",
        "scent",
    }
