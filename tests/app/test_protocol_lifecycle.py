"""Lifecycle paths, loops, absorbing states and boundaries of the phase machine.

Stage 4A enforces phase ORDER only. Phase names that will later carry protocol
payloads - COMMIT_SENT, ACKNOWLEDGED, REVEAL, FINAL_AUDIT - carry none here, and
the machine owns no game state, no step count and no local action.
"""

import pytest

from mars777_police.app.state_machine import (
    IllegalTransitionError,
    ProtocolMachine,
    ProtocolPhase,
)

P = ProtocolPhase
TURN = (P.TURN_DECISION, P.COMMIT_SENT, P.ACKNOWLEDGED, P.REVEAL, P.VALIDATING, P.TURN_COMPLETE)


def _walk(start: ProtocolPhase, path: tuple[ProtocolPhase, ...]) -> ProtocolMachine:
    machine = ProtocolMachine(start)
    for phase in path:
        machine = machine.advance(phase)
    return machine


def test_the_happy_path_from_boot_to_report_ready() -> None:
    machine = _walk(
        P.BOOT,
        (
            P.STEP0_NEGOTIATION,
            P.CONFIG_NEGOTIATION,
            P.CONFIG_LOCKED,
            P.READY,
            *TURN,
            P.SUBGAME_COMPLETE,
            P.SERIES_COMPLETE,
            P.FINAL_AUDIT,
            P.REPORT_READY,
        ),
    )
    assert machine.phase is P.REPORT_READY
    assert machine.is_absorbing


def test_the_documented_turn_loop_repeats() -> None:
    machine = _walk(P.READY, TURN)
    for _ in range(3):
        machine = _walk(machine.phase, TURN)
        assert machine.phase is P.TURN_COMPLETE


def test_the_documented_sub_game_loop_returns_to_ready() -> None:
    machine = _walk(P.TURN_COMPLETE, (P.SUBGAME_COMPLETE, P.READY))
    assert machine.phase is P.READY
    machine = _walk(machine.phase, (P.SUBGAME_COMPLETE, P.SERIES_COMPLETE))
    assert machine.phase is P.SERIES_COMPLETE


def test_a_sub_game_may_complete_directly_from_ready() -> None:
    # Frozen table: READY -> TURN_DECISION, SUBGAME_COMPLETE.
    assert ProtocolMachine(P.READY).advance(P.SUBGAME_COMPLETE).phase is P.SUBGAME_COMPLETE


def test_no_phase_skipping_inside_the_turn() -> None:
    # R1: COMMIT_SENT cannot reach REVEAL without ACKNOWLEDGED.
    with pytest.raises(IllegalTransitionError):
        ProtocolMachine(P.COMMIT_SENT).advance(P.REVEAL)
    with pytest.raises(IllegalTransitionError):
        ProtocolMachine(P.READY).advance(P.VALIDATING)


def test_no_counted_turn_before_the_config_lock() -> None:
    # R3: no turn phase is reachable from the negotiation phases.
    for source in (P.BOOT, P.STEP0_NEGOTIATION, P.CONFIG_NEGOTIATION):
        for target in TURN:
            with pytest.raises(IllegalTransitionError):
                ProtocolMachine(source).advance(target)


def test_no_backwards_transition() -> None:
    for source, target in (
        (P.CONFIG_LOCKED, P.BOOT),
        (P.REVEAL, P.COMMIT_SENT),
        (P.SERIES_COMPLETE, P.SUBGAME_COMPLETE),
        (P.FINAL_AUDIT, P.READY),
    ):
        with pytest.raises(IllegalTransitionError):
            ProtocolMachine(source).advance(target)
