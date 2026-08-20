"""That no benchmark opponent knows anything production would not let it know.

An opponent that cheats produces evidence about a game nobody is playing. The
defence is structural: every policy is handed one `Observation`, whose four
members are the board, its own cell, its own quota and its own folded belief -
and which has no field an opponent cell, a nonce, an intent or a future draw
could arrive in.
"""

import ast
from dataclasses import fields
from pathlib import Path

from research.configs import corpus
from research.game import SubGame
from research.opponents import FAMILIES, opponent

from mars777_police.app.sealed_record_values import ActorRole
from mars777_police.domain.observation import Observation

RESEARCH = Path(__file__).resolve().parents[2] / "research"

FORBIDDEN_KNOWLEDGE = (
    "opponent_position",
    "thief_cell",
    "police_cell",
    "nonce",
    "intent",
    "commitment",
    "future",
    "cell_of",
)


def symbols(name: str) -> set[str]:
    tree = ast.parse((RESEARCH / name).read_text(encoding="utf-8"))
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            found.add(node.id)
        elif isinstance(node, ast.Attribute):
            found.add(node.attr)
    return found


def test_the_observation_still_has_nowhere_to_put_an_opponent() -> None:
    assert {one.name for one in fields(Observation)} == {
        "board",
        "own_position",
        "quota",
        "scent",
    }


def test_no_opponent_policy_names_anything_it_may_not_know() -> None:
    found = symbols("opponents.py")

    for forbidden in FORBIDDEN_KNOWLEDGE:
        assert not any(forbidden in one for one in found), forbidden


def test_no_opponent_policy_reads_a_random_stream_or_a_clock() -> None:
    body = (RESEARCH / "opponents.py").read_text(encoding="utf-8")

    for forbidden in ("import random", "random.", "time.", "datetime"):
        assert forbidden not in body


def test_every_family_decides_from_an_observation_and_nothing_else() -> None:
    config = corpus()[0]
    game = SubGame(config, opponent("pursuit", 5, ActorRole.POLICE), opponent("evasive", 5))
    observation = game.observation(ActorRole.THIEF)

    for family in FAMILIES:
        action = opponent(family, 5).choose_action(observation)
        assert action is not None


def test_a_policy_cannot_reach_the_game_that_is_running_it() -> None:
    """The harness passes a value, never itself: there is no handle to abuse."""
    body = (RESEARCH / "game.py").read_text(encoding="utf-8")

    assert "choose_action(self.observation(" in body
    assert "choose_action(self)" not in body


def test_each_side_folds_only_what_the_other_side_emitted() -> None:
    config = corpus()[0]
    game = SubGame(config, opponent("pursuit", 6, ActorRole.POLICE), opponent("evasive", 6))
    game.play_round()

    police_heard = game.trail.source_for(ActorRole.POLICE).emissions
    thief_heard = game.trail.source_for(ActorRole.THIEF).emissions

    assert len(police_heard) == 1
    assert len(thief_heard) == 1
    assert police_heard != thief_heard


def test_a_silent_opening_round_carries_no_belief_at_all() -> None:
    config = corpus()[0]
    game = SubGame(config, opponent("pursuit", 7, ActorRole.POLICE), opponent("evasive", 7))

    assert game.observation(ActorRole.POLICE).scent.has_evidence is False


def test_research_never_imports_the_sibling_repository() -> None:
    for path in RESEARCH.glob("*.py"):
        body = path.read_text(encoding="utf-8")
        assert "mars777_thief" not in body, path.name
