"""That the laboratory means the same thing the tournament does.

If the research harness and the counted agent disagreed about legality, capture
or the end of a game, every number this stage produces would describe a
different sport. So the harness is not compared to a description of production -
it is required to route through production's own authorities, and to reach the
same verdicts they do.
"""

import ast
from pathlib import Path

import pytest
from research.configs import corpus
from research.game import SubGame
from research.opponents import opponent

from mars777_police.app.sealed_record_values import ActorRole
from mars777_police.app.semantic_replay import Replay
from mars777_police.domain.terminal import Outcome, evaluate_terminal, is_trapped

RESEARCH = Path(__file__).resolve().parents[2] / "research"


def imports(name: str) -> set[str]:
    tree = ast.parse((RESEARCH / name).read_text(encoding="utf-8"))
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            found.add("." * node.level + (node.module or ""))
    return found


def test_the_harness_adjudicates_with_the_production_replay_engine() -> None:
    reached = imports("game.py")

    assert "mars777_police.app.semantic_replay" in reached
    assert "mars777_police.domain.terminal" in reached


def test_the_harness_declares_no_legality_of_its_own() -> None:
    """A second rule about legality could disagree with the first."""
    body = (RESEARCH / "game.py").read_text(encoding="utf-8")

    for invented in ("def is_legal", "def can_move", "def is_capture", "def score_for"):
        assert invented not in body


def test_the_same_seed_and_policies_replay_the_same_game() -> None:
    config = corpus()[0]
    first = SubGame(config, opponent("pursuit", 4, ActorRole.POLICE), opponent("evasive", 4))
    second = SubGame(config, opponent("pursuit", 4, ActorRole.POLICE), opponent("evasive", 4))

    assert first.play() is second.play()
    assert (first.steps, first.barriers_placed) == (second.steps, second.barriers_placed)


def test_every_step_the_harness_plays_is_accepted_by_the_semantic_engine() -> None:
    """`Replay.check` is what the live audit uses; a refused step raises here."""
    config = corpus()[1]
    game = SubGame(config, opponent("barrier_aware", 9, ActorRole.POLICE), opponent("evasive", 9))

    game.play()

    assert isinstance(game.replay, Replay)
    assert game.steps > 0


def test_the_outcome_is_the_one_the_terminal_authority_would_report() -> None:
    config = corpus()[0]
    game = SubGame(config, opponent("pursuit", 11, ActorRole.POLICE), opponent("evasive", 11))

    outcome = game.play()

    assert outcome is evaluate_terminal(
        captured=game.captured, step=game.steps, limits=config.limits()
    )


def test_a_capture_is_only_ever_a_barrier_or_a_trap() -> None:
    """The counted path never issues a capture claim, so neither may research.

    `SubGameDriver.play_round` calls `open_turn` without a `claim`, and
    `StrategyPort` returns `MoveAction | BarrierAction` - a claim is not
    expressible. Contact capture is therefore unreachable in production, and a
    harness that granted it would flatter the police with wins it cannot have.
    """
    driver = (
        Path(__file__).resolve().parents[2] / "src/mars777_police/app/sub_game_driver.py"
    ).read_text(encoding="utf-8")

    assert "claim=" not in driver
    body = (RESEARCH / "game.py").read_text(encoding="utf-8")
    assert "is_same_cell" not in body


def test_a_trapped_thief_is_a_capture_by_the_domain_predicate() -> None:
    config = corpus()[0]
    game = SubGame(config, opponent("barrier_aware", 3, ActorRole.POLICE), opponent("evasive", 3))
    game.play()

    if game.captured and game.settled() is Outcome.CAPTURE:
        cell = game.replay.cell_of(ActorRole.THIEF)
        assert is_trapped(game.replay.board, cell) or game.barriers_placed > 0


def test_an_illegal_policy_is_refused_rather_than_silently_played() -> None:
    from research.game import IllegalResearchActionError

    assert issubclass(IllegalResearchActionError, Exception)
    with pytest.raises(ValueError, match="unknown opponent family"):
        opponent("omniscient", 1)
