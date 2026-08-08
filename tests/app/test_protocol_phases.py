"""The frozen protocol phase inventory (`STATE_MACHINE.md` §1/§2).

The expected lists below are transcribed **literally** from the frozen
architecture, not derived from the implementation, so a drift in either
direction fails.
"""

from mars777_police.app.state_machine import (
    FAULT_PHASES,
    NORMAL_PHASES,
    ProtocolPhase,
)

# STATE_MACHINE.md §2, in table order.
EXPECTED_NORMAL = (
    "BOOT",
    "STEP0_NEGOTIATION",
    "CONFIG_NEGOTIATION",
    "CONFIG_LOCKED",
    "READY",
    "TURN_DECISION",
    "COMMIT_SENT",
    "ACKNOWLEDGED",
    "REVEAL",
    "VALIDATING",
    "TURN_COMPLETE",
    "SUBGAME_COMPLETE",
    "SERIES_COMPLETE",
    "FINAL_AUDIT",
    "REPORT_READY",
)
# STATE_MACHINE.md §1: "terminal / fault: FAILED · TAMPERED · TECHNICAL_LOSS".
EXPECTED_FAULT = ("FAILED", "TAMPERED", "TECHNICAL_LOSS")


def test_the_normal_lifecycle_states_are_exactly_the_frozen_fifteen() -> None:
    assert tuple(p.value for p in NORMAL_PHASES) == EXPECTED_NORMAL
    assert len(NORMAL_PHASES) == 15


def test_the_fault_states_are_exactly_the_frozen_three() -> None:
    assert tuple(p.value for p in FAULT_PHASES) == EXPECTED_FAULT
    assert len(FAULT_PHASES) == 3


def test_there_are_exactly_eighteen_phases_and_no_others() -> None:
    assert {p.value for p in ProtocolPhase} == set(EXPECTED_NORMAL) | set(EXPECTED_FAULT)
    assert len(list(ProtocolPhase)) == 18


def test_no_extra_or_missing_phase() -> None:
    implemented = {p.value for p in ProtocolPhase}
    expected = set(EXPECTED_NORMAL) | set(EXPECTED_FAULT)
    assert implemented - expected == set()
    assert expected - implemented == set()


def test_phase_values_are_unique_and_match_their_names() -> None:
    values = [p.value for p in ProtocolPhase]
    assert len(values) == len(set(values))
    for phase in ProtocolPhase:
        assert phase.name == phase.value


def test_normal_and_fault_phases_are_disjoint_and_cover_everything() -> None:
    normal, fault = set(NORMAL_PHASES), set(FAULT_PHASES)
    assert normal & fault == set()
    assert normal | fault == set(ProtocolPhase)


def test_the_inventory_ordering_is_a_stable_tuple() -> None:
    assert isinstance(NORMAL_PHASES, tuple)
    assert isinstance(FAULT_PHASES, tuple)
    assert tuple(p.value for p in NORMAL_PHASES) == EXPECTED_NORMAL


def test_an_arbitrary_string_is_not_a_phase() -> None:
    import pytest

    for token in ("BOOTED", "boot", "COMMIT", "READY ", ""):
        with pytest.raises(ValueError, match="is not a valid"):
            ProtocolPhase(token)
