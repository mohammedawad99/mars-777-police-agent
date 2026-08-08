"""Exhaustive all-pairs audit of the frozen transition graph.

`EXPECTED_EDGES` is transcribed literally from the "Allowed next" column of
`STATE_MACHINE.md` §2. Every ordered pair of phases is then tried, so a hidden
edge or a missing edge cannot survive.
"""

import dataclasses
import itertools

import pytest

from mars777_police.app.state_machine import (
    IllegalTransitionError,
    ProtocolMachine,
    ProtocolPhase,
)

P = ProtocolPhase

# STATE_MACHINE.md §2 "Allowed next", verbatim. "(terminal)" => no successors.
EXPECTED_EDGES: dict[str, tuple[str, ...]] = {
    "BOOT": ("STEP0_NEGOTIATION", "FAILED"),
    "STEP0_NEGOTIATION": ("CONFIG_NEGOTIATION", "FAILED"),
    "CONFIG_NEGOTIATION": ("CONFIG_LOCKED", "FAILED"),
    "CONFIG_LOCKED": ("READY", "FAILED"),
    "READY": ("TURN_DECISION", "SUBGAME_COMPLETE"),
    "TURN_DECISION": ("COMMIT_SENT", "FAILED"),
    "COMMIT_SENT": ("ACKNOWLEDGED", "FAILED", "TECHNICAL_LOSS"),
    "ACKNOWLEDGED": ("REVEAL", "FAILED"),
    "REVEAL": ("VALIDATING", "FAILED", "TECHNICAL_LOSS"),
    "VALIDATING": ("TURN_COMPLETE", "TAMPERED", "TECHNICAL_LOSS"),
    "TURN_COMPLETE": ("TURN_DECISION", "SUBGAME_COMPLETE"),
    "SUBGAME_COMPLETE": ("READY", "SERIES_COMPLETE"),
    "SERIES_COMPLETE": ("FINAL_AUDIT",),
    "FINAL_AUDIT": ("REPORT_READY", "TAMPERED"),
    "REPORT_READY": (),
    "FAILED": (),
    "TAMPERED": (),
    "TECHNICAL_LOSS": ("SUBGAME_COMPLETE",),
}


def test_the_expected_graph_covers_every_phase_exactly_once() -> None:
    assert set(EXPECTED_EDGES) == {p.value for p in ProtocolPhase}
    assert sum(len(v) for v in EXPECTED_EDGES.values()) == 31


@pytest.mark.parametrize("source", sorted(EXPECTED_EDGES))
def test_allowed_next_matches_the_frozen_table(source: str) -> None:
    machine = ProtocolMachine(P(source))
    assert tuple(p.value for p in machine.allowed_next()) == EXPECTED_EDGES[source]


def test_every_documented_edge_succeeds() -> None:
    for source, targets in EXPECTED_EDGES.items():
        for target in targets:
            result = ProtocolMachine(P(source)).advance(P(target))
            assert result.phase is P(target)


def test_all_pairs_success_exactly_on_the_frozen_edge_set() -> None:
    allowed = 0
    rejected = 0
    for source, target in itertools.product(ProtocolPhase, repeat=2):
        machine = ProtocolMachine(source)
        legal = target.value in EXPECTED_EDGES[source.value]
        if legal:
            assert machine.advance(target).phase is target
            allowed += 1
        else:
            with pytest.raises(IllegalTransitionError):
                machine.advance(target)
            rejected += 1
    assert allowed == 31
    assert rejected == 18 * 18 - 31


def test_no_phase_may_transition_to_itself() -> None:
    for phase in ProtocolPhase:
        assert phase.value not in EXPECTED_EDGES[phase.value]
        with pytest.raises(IllegalTransitionError):
            ProtocolMachine(phase).advance(phase)


def test_a_rejected_transition_leaves_the_machine_unchanged() -> None:
    machine = ProtocolMachine(P.READY)
    with pytest.raises(IllegalTransitionError):
        machine.advance(P.REVEAL)
    assert machine.phase is P.READY


def test_a_successful_transition_returns_a_new_value() -> None:
    machine = ProtocolMachine(P.BOOT)
    moved = machine.advance(P.STEP0_NEGOTIATION)
    assert moved is not machine
    assert machine.phase is P.BOOT
    with pytest.raises(dataclasses.FrozenInstanceError):
        machine.phase = P.FAILED  # type: ignore[misc]


def test_the_error_names_the_source_and_target_safely() -> None:
    with pytest.raises(IllegalTransitionError) as excinfo:
        ProtocolMachine(P.BOOT).advance(P.REVEAL)
    message = str(excinfo.value)
    assert "BOOT" in message and "REVEAL" in message
    for secret in ("nonce", "key", "hash", "token", "opponent"):
        assert secret not in message.lower()


def test_a_non_phase_target_is_rejected() -> None:
    with pytest.raises(IllegalTransitionError):
        ProtocolMachine(P.BOOT).advance("STEP0_NEGOTIATION")  # type: ignore[arg-type]
    with pytest.raises(IllegalTransitionError):
        ProtocolMachine(P.BOOT).advance(None)  # type: ignore[arg-type]
