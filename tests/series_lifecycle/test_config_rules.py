"""One projection from a locked config to the rules a sub-game plays under.

The live series and the final audit must not disagree about what a config
*means*. Before this module the only implementation lived in `semantic_review`,
which would have made a gameplay driver depend on the audit; the projection is
neutral, so it moved here and the audit now consumes the same function.

Equivalence is asserted rather than assumed: every test below compares the
shared authority against the exact expression `semantic_review.rules_for` used,
over an ordinary config and over its App-F edges.
"""

import dataclasses

import pytest
from r16_builders import config

from mars777_police.app.config_rules import limits_of, opening_truth, rules_of
from mars777_police.app.sealed_record_values import ActorRole
from mars777_police.domain.board import Position
from mars777_police.domain.config_model import GridConfig
from mars777_police.domain.config_sections import BoardAndAgentsTerms, MovementAndBarrierTerms

CONFIG = config()


def _with_board(**terms: object) -> object:
    return dataclasses.replace(
        CONFIG,
        board_and_agents=dataclasses.replace(
            CONFIG.board_and_agents,
            **terms,  # type: ignore[arg-type]
        ),
    )


def test_only_one_config_to_rules_implementation_exists() -> None:
    """The audit consumes the shared projection; it defines none of its own."""
    from pathlib import Path

    from mars777_police.app import semantic_review

    assert not hasattr(semantic_review, "rules_for")
    builders = [
        path
        for path in Path("src/mars777_police").rglob("*.py")
        if "GridConfig.from_grid_size" in path.read_text(encoding="utf-8")
    ]
    assert [path.name for path in builders] == ["config_rules.py"]


def test_the_closure_path_uses_the_shared_projection() -> None:
    import inspect

    from mars777_police.app import sub_game_closure

    source = inspect.getsource(sub_game_closure)
    assert "config_rules" in source and "semantic_review import review_sub_game" in source


def test_it_projects_the_locked_geometry_quota_and_starts() -> None:
    rules = rules_of(CONFIG)
    board = CONFIG.board_and_agents
    grid = GridConfig.from_grid_size(board.grid_size, board.axis_start_index)
    assert rules.board == grid.to_board()
    assert rules.quota.max_barriers == CONFIG.movement_and_barriers.max_barriers
    assert rules.cop_start == board.cop_start
    assert rules.thief_start == board.thief_start


@pytest.mark.parametrize(
    "terms",
    [
        {"grid_size": 7},
        {"grid_size": 12},
        {"axis_start_index": 0},
        {"cop_start": Position(0, 0), "thief_start": Position(6, 6)},
    ],
)
def test_edge_configs_project_identically_to_the_audits_expectation(terms: dict) -> None:
    one = _with_board(**terms)
    projected = rules_of(one)  # type: ignore[arg-type]
    board = one.board_and_agents  # type: ignore[attr-defined]
    grid = GridConfig.from_grid_size(board.grid_size, board.axis_start_index)
    assert projected.board == grid.to_board()
    assert projected.start_for(ActorRole.POLICE) == board.cop_start
    assert projected.start_for(ActorRole.THIEF) == board.thief_start


def test_limits_come_from_the_locked_movement_terms() -> None:
    limits = limits_of(CONFIG)
    terms = CONFIG.movement_and_barriers
    assert limits.max_moves == terms.max_moves
    assert limits.survival_threshold == terms.survival_threshold


def test_limits_track_a_raised_negotiated_ceiling() -> None:
    raised = dataclasses.replace(
        CONFIG,
        movement_and_barriers=MovementAndBarrierTerms(
            CONFIG.movement_and_barriers.move_set, 20, 60, 40
        ),
    )
    limits = limits_of(raised)
    assert (limits.max_moves, limits.survival_threshold) == (60, 40)
    assert rules_of(raised).quota.max_barriers == 20


def test_the_opening_truth_is_this_sub_games_start_and_nothing_carried() -> None:
    for role in ActorRole:
        truth = opening_truth(CONFIG, role)
        assert truth.completed_steps == 0
        assert truth.own_position == rules_of(CONFIG).start_for(role)
        assert truth.board.blocked == frozenset()


def test_the_opening_truth_follows_a_reconfigured_start_cell() -> None:
    moved = _with_board(cop_start=Position(2, 2), thief_start=Position(2, 3))
    assert opening_truth(moved, ActorRole.POLICE).own_position == Position(2, 2)  # type: ignore[arg-type]
    assert opening_truth(moved, ActorRole.THIEF).own_position == Position(2, 3)  # type: ignore[arg-type]


def test_the_board_terms_still_refuse_an_illegal_grid() -> None:
    from mars777_police.domain.config_sections import InvalidConfigSectionError

    with pytest.raises(InvalidConfigSectionError):
        BoardAndAgentsTerms(6, 2, Position(0, 0), Position(0, 1), "top-left", 0)
