"""Absorbing states, documented failure edges, reachability and determinism.

`STATE_MACHINE.md` R5 ("terminal is terminal") plus the "Allowed next" column,
which names no successor for REPORT_READY, FAILED, TAMPERED or TECHNICAL_LOSS.
"""

import os
import subprocess
import sys

import pytest

from mars777_police.app import state_machine
from mars777_police.app.state_machine import (
    FAULT_PHASES,
    IllegalTransitionError,
    ProtocolMachine,
    ProtocolPhase,
)

P = ProtocolPhase
ABSORBING = (P.REPORT_READY, P.FAILED, P.TAMPERED)
PROBE = (
    "from mars777_police.app.state_machine import ProtocolMachine, ProtocolPhase as P;"
    "m=ProtocolMachine(P.BOOT);"
    "print([p.value for p in m.allowed_next()],"
    " m.advance(P.STEP0_NEGOTIATION).machine.phase.value)"
)


@pytest.mark.parametrize("phase", ABSORBING)
def test_absorbing_states_reject_every_further_transition(phase: ProtocolPhase) -> None:
    machine = ProtocolMachine(phase)
    assert machine.allowed_next() == ()
    assert machine.is_absorbing
    for target in ProtocolPhase:
        with pytest.raises(IllegalTransitionError):
            machine.advance(target)
        assert machine.phase is phase


def test_the_three_fault_states_are_distinct_and_not_interchangeable() -> None:
    assert len(set(FAULT_PHASES)) == 3
    for source, target in (
        (P.FAILED, P.TAMPERED),
        (P.TAMPERED, P.TECHNICAL_LOSS),
        (P.TECHNICAL_LOSS, P.FAILED),
    ):
        with pytest.raises(IllegalTransitionError):
            ProtocolMachine(source).advance(target)


def test_tampered_never_returns_to_play() -> None:
    # R5, and PDF p.75: no appeal, no retroactive correction.
    machine = ProtocolMachine(P.TAMPERED)
    assert machine.is_absorbing
    for target in ProtocolPhase:
        with pytest.raises(IllegalTransitionError):
            machine.advance(target)
    with pytest.raises(IllegalTransitionError):
        machine.advance(P.SUBGAME_COMPLETE)


def test_failed_never_returns_to_play() -> None:
    machine = ProtocolMachine(P.FAILED)
    assert machine.is_absorbing
    with pytest.raises(IllegalTransitionError):
        machine.advance(P.SUBGAME_COMPLETE)


def test_failure_states_are_entered_only_from_documented_sources() -> None:
    allowed = {
        P.FAILED: {
            P.BOOT,
            P.STEP0_NEGOTIATION,
            P.CONFIG_NEGOTIATION,
            P.CONFIG_LOCKED,
            P.TURN_DECISION,
            P.COMMIT_SENT,
            P.ACKNOWLEDGED,
            P.REVEAL,
        },
        P.TAMPERED: {P.VALIDATING, P.FINAL_AUDIT},
        P.TECHNICAL_LOSS: {P.COMMIT_SENT, P.REVEAL, P.VALIDATING},
    }
    for fault, sources in allowed.items():
        for phase in ProtocolPhase:
            if phase in sources:
                assert ProtocolMachine(phase).advance(fault).machine.phase is fault
            else:
                with pytest.raises(IllegalTransitionError):
                    ProtocolMachine(phase).advance(fault)


def test_no_generic_fail_escape_hatch_exists() -> None:
    for name in ("fail", "abort", "force", "reset", "halt"):
        assert not hasattr(ProtocolMachine, name)
        assert not hasattr(state_machine, name)


def test_every_phase_is_reachable_from_boot() -> None:
    seen, stack = {P.BOOT}, [P.BOOT]
    while stack:
        for target in ProtocolMachine(stack.pop()).allowed_next():
            if target not in seen:
                seen.add(target)
                stack.append(target)
    assert seen == set(ProtocolPhase)


def test_no_normal_phase_requires_passing_through_a_fault_state() -> None:
    seen, stack = {P.BOOT}, [P.BOOT]
    while stack:
        for target in ProtocolMachine(stack.pop()).allowed_next():
            if target not in seen and target not in FAULT_PHASES:
                seen.add(target)
                stack.append(target)
    assert seen == set(ProtocolPhase) - set(FAULT_PHASES)


def test_equal_inputs_produce_equal_outputs() -> None:
    assert ProtocolMachine(P.READY) == ProtocolMachine(P.READY)
    assert ProtocolMachine(P.READY).advance(P.TURN_DECISION) == (
        ProtocolMachine(P.READY).advance(P.TURN_DECISION)
    )
    for _ in range(5):
        assert ProtocolMachine(P.VALIDATING).allowed_next() == (
            P.TURN_COMPLETE,
            P.TAMPERED,
            P.TECHNICAL_LOSS,
        )


def test_results_are_stable_under_python_hash_randomisation() -> None:
    outputs = set()
    for seed in ("0", "1", "424242"):
        run = subprocess.run(
            [sys.executable, "-c", PROBE],
            capture_output=True,
            text=True,
            env=dict(os.environ, PYTHONHASHSEED=seed),
            check=True,
        )
        outputs.add(run.stdout.strip())
    assert len(outputs) == 1
