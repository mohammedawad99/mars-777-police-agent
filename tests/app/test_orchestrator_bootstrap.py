"""Bootstrap provenance and the trusted-constructor boundary.

`LocalOrchestrator.start()` is the only runtime bootstrap: BOOT, first sub-game,
a validated `SeriesConfig`, and no fabricated evidence because there is no
NULL -> BOOT transition. Direct dataclass construction is the same kind of
**trusted internal snapshot / test primitive** that `ProtocolMachine`'s
constructor already is (`STATE_MACHINE.md` §4 "Bootstrap"), so it is proved
here that no production module uses it.

The frozen architecture defines no untrusted restoration, and none is
implemented. The rule recorded for the future: untrusted network input, JSON,
artifacts, disk, replay and peer messages must never drive `sub_game`,
`ProtocolMachine.phase` or `SeriesConfig` through these trusted constructors -
a later restoration path must revalidate `num_games == 6` and `sub_game` in
1..6, and then authenticate provenance per PRD-06 / replay.
"""

import ast
import pathlib

import pytest

from mars777_police.app.orchestrator import (
    IllegalSubGameBranchError,
    LocalOrchestrator,
    OrchestratorResult,
)
from mars777_police.app.state_machine import ProtocolMachine, ProtocolPhase
from mars777_police.domain.config_model import SeriesConfig

P = ProtocolPhase
SERIES = SeriesConfig()


def _production_calls(name: str) -> list[str]:
    return [
        f"{path}:{node.lineno}"
        for path in sorted(pathlib.Path("src").rglob("*.py"))
        for node in ast.walk(ast.parse(path.read_text()))
        if isinstance(node, ast.Call) and getattr(node.func, "id", None) == name
    ]


def test_the_normal_bootstrap_is_start_at_boot_and_the_first_sub_game() -> None:
    orchestrator = LocalOrchestrator.start(SERIES)
    assert orchestrator.machine == ProtocolMachine.start()
    assert orchestrator.machine.phase is P.BOOT
    assert orchestrator.sub_game == 1
    assert orchestrator.series == SERIES


def test_the_bootstrap_emits_no_transition_evidence() -> None:
    started = LocalOrchestrator.start(SERIES)
    assert isinstance(started, LocalOrchestrator)
    assert not isinstance(started, OrchestratorResult)
    assert not hasattr(started, "evidence")


def test_no_production_module_constructs_an_orchestrator_directly() -> None:
    """Nothing in production bypasses start(), so the constructor stays trusted-only."""
    assert _production_calls("LocalOrchestrator") == []


def test_untrusted_values_cannot_shortcut_the_validated_cursor() -> None:
    for forged in (0, 7, 99, "3", 3.0, None, True):
        with pytest.raises(IllegalSubGameBranchError):
            LocalOrchestrator(ProtocolMachine.start(), SERIES, forged)  # type: ignore[arg-type]


def test_untrusted_values_cannot_shortcut_the_validated_series() -> None:
    for forged in (6, {"num_games": 6}, "6", None):
        with pytest.raises(IllegalSubGameBranchError):
            LocalOrchestrator(ProtocolMachine.start(), forged, 1)  # type: ignore[arg-type]
        with pytest.raises(IllegalSubGameBranchError):
            LocalOrchestrator.start(forged)  # type: ignore[arg-type]


def test_no_persistence_or_restoration_api_exists_yet() -> None:
    for name in ("restore", "from_json", "load", "rehydrate", "parse", "deserialize"):
        assert not hasattr(LocalOrchestrator, name)
