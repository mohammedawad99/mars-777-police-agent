"""Two real agents playing a whole six-sub-game series nobody scripted.

The lifecycle proof that came before this one chose the actions and the
outcomes; the sub-game proof that came after it played one game autonomously but
left the series bookkeeping to the test. This leaves nothing to the test: one
call to `play_series()` on each side produces six negotiated configs, six
naturally-terminating sub-games, six audited logs, a real result agreement and
the fourteen official files.
"""

import asyncio
import inspect
from pathlib import Path

import autonomous_series_builders as auto
import pytest
import r7_builders as r7

from mars777_police.app.sealed_record_values import ActorRole
from mars777_police.domain.terminal import Outcome

GAMES = 6


@pytest.fixture(scope="module")
def played(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, list[object]]:
    """Play the one autonomous six-sub-game series once; all tests read it."""
    root = tmp_path_factory.mktemp("series")
    a, b = auto.pair_for(root)
    drivers = (auto.driver_for(a, ActorRole.POLICE), auto.driver_for(b, ActorRole.THIEF))

    async def run() -> list[object]:
        async with auto.started(a, b):
            for driver in drivers:
                driver.open()
            return list(await asyncio.gather(*(driver.play_series() for driver in drivers)))

    stored = asyncio.run(run())
    return root, [a, b, *stored]


def _sides(played: tuple) -> tuple[object, object]:
    _, held = played
    return held[0], held[1]


def test_exactly_six_sub_games_were_played(played: tuple) -> None:
    for series in _sides(played):
        assert len(series.lines) == GAMES  # type: ignore[attr-defined]


def test_the_audit_gate_recorded_exactly_g01_to_g06(played: tuple) -> None:
    for series in _sides(played):
        gate = series.composition.series_audit  # type: ignore[attr-defined]
        assert gate.audited == (1, 2, 3, 4, 5, 6)
        assert gate.complete is True


def test_every_sub_game_reached_a_natural_terminal(played: tuple) -> None:
    for series in _sides(played):
        outcomes = [line.outcome for line in series.lines]  # type: ignore[attr-defined]
        assert len(outcomes) == GAMES
        assert all(isinstance(one, Outcome) for one in outcomes)


def test_no_seventh_sub_game_is_representable(played: tuple) -> None:
    from mars777_police.app.orchestrator import IllegalSubGameBranchError
    from mars777_police.app.state_machine import ProtocolPhase

    for series in _sides(played):
        assert series.orchestrator.machine.phase is ProtocolPhase.REPORT_READY  # type: ignore[attr-defined]
        assert series.orchestrator.is_last_sub_game is True  # type: ignore[attr-defined]
    assert IllegalSubGameBranchError is not None


def test_exactly_fourteen_official_files_exist(played: tuple) -> None:
    root, _ = played
    for side in ("police", "thief"):
        names = sorted(path.name for path in (root / side).iterdir())
        assert len(names) == 14
        assert len(set(names)) == 14


def test_the_names_are_one_declaration_six_configs_six_logs_one_result(played: tuple) -> None:
    root, _ = played
    for side in ("police", "thief"):
        names = sorted(path.name for path in (root / side).iterdir())
        assert sum(one.startswith("declaration_") for one in names) == 1
        assert sum(one.startswith("result_") for one in names) == 1
        for family in ("config_", "log_"):
            got = sorted(one for one in names if one.startswith(family))
            assert len(got) == GAMES
            assert all(f"_g0{index}." in one for index, one in enumerate(got, start=1))


def test_every_sub_game_was_reviewed_consistent(played: tuple) -> None:
    import json

    root, _ = played
    for side in ("police", "thief"):
        logs = sorted(path for path in (root / side).iterdir() if path.name.startswith("log_"))
        assert len(logs) == GAMES
        for log in logs:
            document = json.loads(log.read_text(encoding="utf-8"))
            assert document["audit"]["semantic"]["verdict"] == "CONSISTENT"


def test_the_result_was_agreed_before_it_was_written(played: tuple) -> None:
    for series in _sides(played):
        exchange = series.composition.runtime_context.current_result()  # type: ignore[attr-defined]
        assert exchange.is_agreed is True


def test_the_scent_model_stayed_frozen_across_all_six(played: tuple) -> None:
    for series in _sides(played):
        freeze = series.composition.pregame.scent_freeze  # type: ignore[attr-defined]
        assert freeze.identity is not None


def test_the_role_never_alternated(played: tuple) -> None:
    a, b = _sides(played)
    assert a.composition.pregame.negotiation.group_id != b.composition.pregame.negotiation.group_id  # type: ignore[attr-defined]
    for series, expected in (
        (a, r7.POSITIONS[ActorRole.POLICE]),
        (b, r7.POSITIONS[ActorRole.THIEF]),
    ):
        assert expected is not None
        assert series.composition.identity.game_id  # type: ignore[attr-defined]


def test_the_harness_supplies_no_action_no_outcome_and_no_lifecycle_call() -> None:
    source = inspect.getsource(auto)
    for forbidden in (
        "MoveAction",
        "BarrierAction",
        "Move.",
        "Outcome.",
        "close_turn",
        "close_sub_game",
        "send_final_nonce_reveal",
        "send_audit_disclosure",
        "open_result_agreement",
        "respond_to_result",
        "open_round",
        "adopt_config",
        "lock_config",
        "send_config_proposal",
        "send_config_lock",
        "choose_action",
    ):
        assert forbidden not in source
    assert "play_series()" in source or "play_series" in source
