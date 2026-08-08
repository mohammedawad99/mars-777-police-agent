"""Every successful transition emits evidence; every illegal one emits none.

`STATE_MACHINE.md` R7 applies to transitions, not to rejected requests: an
illegal request raises and leaves the machine untouched, so no successful
evidence exists for it.
"""

import itertools

import pytest

from mars777_police.app.state_machine import (
    IllegalTransitionError,
    ProtocolMachine,
    ProtocolPhase,
    TransitionEvidence,
    TransitionResult,
)

P = ProtocolPhase


def _edges() -> list[tuple[ProtocolPhase, ProtocolPhase]]:
    return [(s, t) for s in ProtocolPhase for t in ProtocolMachine(s).allowed_next()]


def test_every_legal_edge_emits_exactly_one_consistent_evidence() -> None:
    edges = _edges()
    assert len(edges) == 31
    for source, target in edges:
        before = ProtocolMachine(source)
        result = before.advance(target)
        assert isinstance(result, TransitionResult)
        assert isinstance(result.evidence, TransitionEvidence)
        assert result.evidence.source_phase is source
        assert result.evidence.target_phase is target
        assert result.machine.phase is target
        assert before.phase is source


def test_the_result_can_never_be_internally_inconsistent() -> None:
    with pytest.raises(IllegalTransitionError):
        TransitionResult(
            machine=ProtocolMachine(P.REVEAL),
            evidence=TransitionEvidence(P.COMMIT_SENT, P.ACKNOWLEDGED),
        )
    with pytest.raises(IllegalTransitionError):
        TransitionResult(machine=ProtocolMachine(P.BOOT), evidence=P.BOOT)  # type: ignore[arg-type]


def test_illegal_edges_raise_and_emit_nothing() -> None:
    illegal = 0
    legal = {(s, t) for s, t in _edges()}
    for source, target in itertools.product(ProtocolPhase, repeat=2):
        if (source, target) in legal:
            continue
        machine = ProtocolMachine(source)
        with pytest.raises(IllegalTransitionError):
            machine.advance(target)
        assert machine.phase is source
        illegal += 1
    assert illegal == 293


def test_no_evidence_less_transition_api_exists() -> None:
    for name in (
        "advance_without_evidence",
        "raw_advance",
        "unsafe_advance",
        "transition",
        "step",
        "goto",
    ):
        assert not hasattr(ProtocolMachine, name)


def test_equal_inputs_produce_equal_results() -> None:
    first = ProtocolMachine(P.READY).advance(P.TURN_DECISION)
    second = ProtocolMachine(P.READY).advance(P.TURN_DECISION)
    assert first == second
    assert first.evidence == second.evidence
    assert first.machine == second.machine
