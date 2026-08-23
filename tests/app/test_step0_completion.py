"""The Step-0 completion gate: both directions, or nothing proceeds.

Having sent our own evidence proves nothing about the peer, and having verified
the peer's proves nothing about ours. Only a snapshot holding **both** subtrees,
produced by a verified exchange, entitles the negotiation runtime to run.
"""

import pytest
from r16_builders import COMMIT_A, GROUP_A, merged, partial

from mars777_police.app.declaration_values import Declaration
from mars777_police.app.state_machine import IllegalTransitionError, ProtocolMachine, ProtocolPhase
from mars777_police.app.step0_runtime import Step0Completion

PARTIAL = partial(GROUP_A, COMMIT_A)


def test_both_directions_complete_is_the_only_complete_state() -> None:
    assert Step0Completion(True, merged()).is_complete


@pytest.mark.parametrize(
    ("sent", "snapshot"),
    [
        (False, None),
        (True, None),
        (False, merged()),
        (True, PARTIAL),
        (False, PARTIAL),
    ],
)
def test_every_incomplete_combination_is_refused(sent: bool, snapshot: Declaration | None) -> None:
    assert not Step0Completion(sent, snapshot).is_complete


def test_sending_our_own_evidence_alone_is_not_completion() -> None:
    assert not Step0Completion(True, None).is_complete


def test_verifying_the_peer_alone_is_not_completion() -> None:
    assert not Step0Completion(False, merged()).is_complete


def test_the_gate_carries_no_phase_and_decides_no_transition() -> None:
    """It reports a fact; the one authoritative graph still owns the step."""
    gate = Step0Completion(True, merged())
    assert not hasattr(gate, "phase")
    assert not hasattr(gate, "advance")


def test_the_frozen_graph_still_owns_the_step_after_step0() -> None:
    machine = ProtocolMachine(ProtocolPhase.STEP0_NEGOTIATION)
    assert machine.advance(ProtocolPhase.CONFIG_NEGOTIATION).machine.phase is (
        ProtocolPhase.CONFIG_NEGOTIATION
    )
    with pytest.raises(IllegalTransitionError):
        machine.advance(ProtocolPhase.CONFIG_LOCKED)


def test_no_sanction_is_attached_to_a_pre_play_failure() -> None:
    from mars777_police.app import step0_runtime

    source = step0_runtime.__doc__ or ""
    assert "technical-loss" in source
    assert not hasattr(step0_runtime, "TECHNICAL_LOSS")
