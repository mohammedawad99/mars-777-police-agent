"""One whole sub-game that nobody scripted, played by two real agents.

Every earlier lifecycle proof handed the turns their actions and the sub-game
its outcome. This one hands over neither: each side's own `BaselineStrategy`
picks its move from an `Observation` built out of its own truth, and the end
event comes back from `domain.terminal` after the real locked survival
threshold. The harness starts two servers and wires two drivers; it decides
nothing about the game.

The terminal is `SURVIVAL` by construction rather than by luck: the Stage-6B
police baseline has no belief, so it places no barrier and declares no capture,
which leaves exactly one source-defined way for this sub-game to end.
"""

import asyncio
import inspect
from pathlib import Path

import autonomous_builders as auto
import pytest
import r7_builders as r7

from mars777_police.domain.terminal import Outcome

THRESHOLD = auto.LIMITS.survival_threshold


@pytest.fixture(scope="module")
def played(tmp_path_factory: pytest.TempPathFactory) -> tuple[Outcome, int, Path]:
    """Play the one autonomous sub-game once; every test reads its result."""
    root = tmp_path_factory.mktemp("autonomous")
    a, b = auto.pair_for(root)
    outcome, rounds = asyncio.run(auto.autonomous(a, b))
    return outcome, rounds, root


def test_the_sub_game_ends_by_natural_survival(played: tuple) -> None:
    outcome, _, _ = played
    assert outcome is Outcome.SURVIVAL


def test_it_ends_at_exactly_the_locked_survival_threshold(played: tuple) -> None:
    _, rounds, _ = played
    assert rounds == THRESHOLD


def test_the_parameters_were_source_compliant_counted_play() -> None:
    assert r7.CONFIG.board_and_agents.grid_size >= 7
    assert auto.LIMITS.max_moves >= 35
    assert auto.LIMITS.survival_threshold >= 35
    assert auto.LIMITS.survival_threshold <= auto.LIMITS.max_moves
    assert auto.QUOTA.max_barriers >= 14


def test_exactly_the_three_partial_series_artifacts_exist(played: tuple) -> None:
    _, _, root = played
    for side in ("police", "thief"):
        names = sorted(path.name for path in (root / side).iterdir())
        assert len(names) == 3
        assert names[0].startswith("config_") and names[1].startswith("declaration_")
        assert names[2].startswith("log_")


def test_no_result_artifact_was_written_for_an_unfinished_series(played: tuple) -> None:
    _, _, root = played
    for side in ("police", "thief"):
        assert not any(path.name.startswith("result_") for path in (root / side).iterdir())


def test_the_final_semantic_review_found_the_game_consistent(played: tuple) -> None:
    import json

    _, _, root = played
    for side in ("police", "thief"):
        log = next(path for path in (root / side).iterdir() if path.name.startswith("log_"))
        document = json.loads(log.read_text(encoding="utf-8"))
        assert document["audit"]["semantic"]["verdict"] == "CONSISTENT"


def test_every_round_was_sealed_under_one_shared_cursor_step(played: tuple) -> None:
    import json

    _, _, root = played
    steps = []
    for side in ("police", "thief"):
        log = next(path for path in (root / side).iterdir() if path.name.startswith("log_"))
        document = json.loads(log.read_text(encoding="utf-8"))
        steps.append(sorted({e["step"] for e in document["entries"] if "step" in e}))
    assert steps[0] == steps[1] == list(range(1, THRESHOLD + 1))


def test_the_harness_supplies_no_action_and_no_outcome() -> None:
    source = inspect.getsource(auto)
    for forbidden in ("MoveAction", "BarrierAction", "Move.", "Outcome.CAPTURE"):
        assert forbidden not in source
    assert "close_sub_game(police)" in source


def test_the_driver_module_holds_no_heuristic_and_no_opponent_truth() -> None:
    from mars777_police.app import sub_game_driver

    code = inspect.getsource(sub_game_driver)
    for forbidden in ("opponent_position", "heatmap", "semantic_replay", "random"):
        assert forbidden not in code.lower().replace("the peer", "")
    assert "self.scent" in code, "the driver passes a source rather than a folded field"
    for folding in ("observed_field", "absorbed", "ScentField", "decay"):
        assert folding not in code, "no scent arithmetic belongs in the turn loop"
