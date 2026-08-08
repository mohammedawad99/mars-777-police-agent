"""What the orchestrator owns - and, mostly, what it does not.

`STATE_OWNERSHIP.md` gives `app.orchestrator` exactly one row of live state in
this stage's scope: **current sub-game index** (lifetime SERIES, reset at series
start). The phase belongs to `app.state_machine`, turn/step and own position to
`domain.truth`, barriers to `domain.barriers`, logs to `infra.logger`. The
prime rule is one authoritative owner per mutable state, so every one of those
facts must be *absent* here rather than mirrored.

`SeriesConfig` is a read-only immutable config projection, not orchestrator
state: `STATE_OWNERSHIP.md` gives the locked config to `protocol.config_lock`
with "all layers (read-only value)" as readers.
"""

import dataclasses

import pytest

from mars777_police.app.orchestrator import (
    IllegalSubGameBranchError,
    LocalOrchestrator,
    OrchestratorResult,
)
from mars777_police.app.state_machine import (
    ProtocolMachine,
    ProtocolPhase,
    TransitionEvidence,
)
from mars777_police.domain.config_model import SeriesConfig

P = ProtocolPhase
SERIES = SeriesConfig()
_NOT_OURS = """
phase current_phase state completed_steps step turn_number turn_cursor position
own_position board truth local_truth barriers barrier_set score scores scent
belief history events evidence_log log logger transitions config_verified
terminal captured survived tampered hash_valid timeout audit_passed more_subgames
role is_police is_thief is_ready is_config_locked is_turn_complete
is_series_complete nonce commitment deadline clock
"""
FORBIDDEN = _NOT_OURS.split()


def _fields(cls: type) -> tuple[str, ...]:
    return tuple(f.name for f in dataclasses.fields(cls))


def test_the_orchestrator_owns_only_the_machine_series_and_cursor() -> None:
    assert _fields(LocalOrchestrator) == ("machine", "series", "sub_game")


def test_the_orchestrator_mirrors_no_other_subsystem_fact() -> None:
    names = set(_fields(LocalOrchestrator))
    for forbidden in FORBIDDEN:
        assert forbidden not in names


def test_the_result_carries_only_the_new_state_and_its_evidence() -> None:
    assert _fields(OrchestratorResult) == ("orchestrator", "evidence")
    for forbidden in FORBIDDEN:
        assert forbidden not in set(_fields(OrchestratorResult))


def test_the_phase_is_read_through_the_machine_never_copied() -> None:
    orchestrator = LocalOrchestrator.start(SERIES)
    assert isinstance(orchestrator.machine, ProtocolMachine)
    assert orchestrator.machine.phase is P.BOOT
    assert not hasattr(orchestrator, "phase")


def test_both_values_are_frozen_slotted_and_value_equal() -> None:
    orchestrator = LocalOrchestrator.start(SERIES)
    with pytest.raises(dataclasses.FrozenInstanceError):
        orchestrator.sub_game = 2  # type: ignore[misc]
    assert not hasattr(orchestrator, "__dict__")
    assert LocalOrchestrator.__slots__ == ("machine", "series", "sub_game")
    assert OrchestratorResult.__slots__ == ("orchestrator", "evidence")
    assert orchestrator == LocalOrchestrator.start(SERIES)


def test_the_bootstrap_is_the_machine_start_at_boot_and_the_first_sub_game() -> None:
    orchestrator = LocalOrchestrator.start(SERIES)
    assert orchestrator.machine == ProtocolMachine.start()
    assert orchestrator.machine.phase is P.BOOT
    assert orchestrator.sub_game == 1
    assert orchestrator.series is SERIES


def test_the_bootstrap_fabricates_no_transition_evidence() -> None:
    """There is no NULL -> BOOT transition, so nothing may be emitted for it."""
    assert isinstance(LocalOrchestrator.start(SERIES), LocalOrchestrator)
    assert not isinstance(LocalOrchestrator.start(SERIES), OrchestratorResult)


def test_the_bootstrap_requires_a_real_validated_series() -> None:
    for bad in (6, "6", None, SeriesConfig):
        with pytest.raises(IllegalSubGameBranchError):
            LocalOrchestrator.start(bad)  # type: ignore[arg-type]


@pytest.mark.parametrize("value", [0, -1, 7, True, 1.0, "1", None])
def test_an_impossible_cursor_cannot_be_constructed(value: object) -> None:
    with pytest.raises(IllegalSubGameBranchError):
        LocalOrchestrator(ProtocolMachine.start(), SERIES, value)  # type: ignore[arg-type]


def test_the_cursor_upper_bound_is_the_fixed_sixth_sub_game() -> None:
    assert LocalOrchestrator(ProtocolMachine.start(), SERIES, 6).sub_game == 6
    for beyond in (7, 8, 11):
        with pytest.raises(IllegalSubGameBranchError):
            LocalOrchestrator(ProtocolMachine.start(), SERIES, beyond)


def test_the_machine_must_be_a_real_protocol_machine() -> None:
    with pytest.raises(IllegalSubGameBranchError):
        LocalOrchestrator(P.BOOT, SERIES, 1)  # type: ignore[arg-type]


def test_a_result_can_never_disagree_with_its_own_new_phase() -> None:
    ready = LocalOrchestrator(ProtocolMachine(P.READY), SERIES, 1)
    with pytest.raises(IllegalSubGameBranchError):
        OrchestratorResult(ready, TransitionEvidence(P.BOOT, P.STEP0_NEGOTIATION))
    with pytest.raises(IllegalSubGameBranchError):
        OrchestratorResult(ready, P.READY)  # type: ignore[arg-type]
    intact = OrchestratorResult(ready, TransitionEvidence(P.CONFIG_LOCKED, P.READY))
    assert intact.evidence.target_phase is intact.orchestrator.machine.phase


def test_no_evidence_history_is_retained() -> None:
    orchestrator = LocalOrchestrator.start(SERIES)
    for name in ("evidence", "trail", "records", "append", "history"):
        assert not hasattr(orchestrator, name)
