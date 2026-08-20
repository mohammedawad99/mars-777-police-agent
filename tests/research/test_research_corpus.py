"""Seeds, configurations and scenarios: what a benchmark varies, and what it may not."""

import pytest
from research.configs import GRID_MINIMUM, corpus
from research.stats import SmallSampleError

from mars777_police.domain.board import Position
from research import seeds


def test_a_seed_is_the_same_number_in_any_process() -> None:
    assert seeds.seed_at("development", 0) == seeds.seed_at("development", 0)
    assert seeds.seed_at("development", 0) != seeds.seed_at("holdout", 0)


def test_a_negative_seed_index_is_refused() -> None:
    with pytest.raises(ValueError, match="not negative"):
        seeds.seed_at("development", -1)


def test_an_empty_bank_is_refused() -> None:
    with pytest.raises(ValueError, match="at least one seed"):
        seeds.bank("development", 0)


def test_every_bank_is_pairwise_disjoint_from_every_other() -> None:
    """Four banks now, including the sealed one, and no seed may appear twice."""
    all_banks = seeds.banks()

    for index, first in enumerate(all_banks):
        for second in all_banks[index + 1 :]:
            assert seeds.disjoint(first, second), f"{first.name} shares a seed with {second.name}"


def test_a_bank_digest_changes_only_when_its_seeds_do() -> None:
    assert seeds.development_bank().digest == seeds.development_bank().digest
    assert seeds.development_bank().digest != seeds.validation_bank().digest


def test_no_configuration_is_below_the_appendix_f_grid_minimum() -> None:
    assert all(one.grid >= GRID_MINIMUM for one in corpus())
    assert 5 not in {one.grid for one in corpus()}


def test_the_corpus_includes_the_appendix_f_example_values_themselves() -> None:
    base = next(one for one in corpus() if one.name == "appendixF-example")

    assert (base.grid, base.quota, base.horizon) == (7, 14, 35)
    assert (base.police_start, base.thief_start) == ((0, 0), (3, 3))
    assert base.fixed_starts is True


def test_a_seed_now_actually_changes_the_scenario() -> None:
    """The first benchmark found the seed inert; this is what stops that returning."""
    from research.scenario import start_cells

    config = corpus()[1]
    openings = {start_cells(config, seed) for seed in range(32)}

    assert len(openings) > 16, "seeds must select genuinely different openings"


def test_the_two_actors_never_start_on_the_same_cell() -> None:
    from research.scenario import start_cells

    for config in corpus():
        for seed in range(64):
            police, thief = start_cells(config, seed)
            assert police != thief


def test_every_opening_is_on_the_board() -> None:
    from research.scenario import start_cells

    for config in corpus():
        board = config.board()
        for seed in range(32):
            for cell in start_cells(config, seed):
                assert board.contains(cell)


def test_the_appendix_example_geometry_ignores_the_seed() -> None:
    from research.scenario import start_cells

    example = next(one for one in corpus() if one.fixed_starts)

    assert start_cells(example, 1) == start_cells(example, 999)
    assert start_cells(example, 1) == (example.cop_cell(), example.thief_cell())


def test_a_bootstrap_below_the_floor_is_refused_directly() -> None:
    from research.stats import bootstrap_interval

    with pytest.raises(SmallSampleError, match="at least"):
        bootstrap_interval((1.0, 2.0))


def test_an_actor_with_no_legal_move_at_all_is_a_terminal_not_a_decision() -> None:
    """Even `STAY` is illegal on a blocked cell, which BAR-004 makes reachable.

    The police may place a barrier on the square it occupies, so an actor whose
    own cell *and* neighbours are blocked has an empty move set. That is a
    terminal the caller settles, never something a policy may guess at.
    """
    from research.opponents import opponent

    from mars777_police.domain.barriers import BarrierQuota
    from mars777_police.domain.board import Board
    from mars777_police.domain.observation import Observation
    from mars777_police.domain.rules import legal_moves

    walls = frozenset({Position(0, 0), Position(0, 1), Position(1, 0)})
    board = Board(rows=7, cols=7, blocked=walls)
    boxed = Observation(board, Position(0, 0), BarrierQuota(max_barriers=14))
    assert legal_moves(board, Position(0, 0)) == ()

    with pytest.raises(ValueError, match="terminal, not a decision"):
        opponent("evasive", 1).choose_action(boxed)


def test_a_policy_that_returns_an_illegal_action_is_refused_by_the_harness() -> None:
    """The harness never plays a step `Replay.check` would reject."""
    from research.game import IllegalResearchActionError, SubGame
    from research.opponents import opponent

    from mars777_police.app.sealed_record_values import ActorRole
    from mars777_police.domain.actions import MoveAction
    from mars777_police.domain.observation import Observation
    from mars777_police.domain.rules import Move

    class Cheat:
        """Always walks north, whether or not north exists."""

        def choose_action(self, observation: Observation) -> MoveAction:
            return MoveAction(Move.N)

    config = corpus()[0]
    game = SubGame(
        config, Cheat(), opponent("evasive", 1, ActorRole.THIEF), Position(0, 0), Position(3, 3)
    )

    with pytest.raises(IllegalResearchActionError, match="ILLEGAL_ACTION"):
        game.play()
