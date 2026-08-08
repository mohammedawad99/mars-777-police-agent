"""The transition-evidence contract (R7) for successful phase transitions.

`STATE_MACHINE.md` R7 requires every transition to emit an evidence record
sufficient for replay. `PROTOCOL_TIMELINE.md` event 10 defines the state
machine's own share of that record as exactly a "phase transition", with
persistence and hashing both marked "—": those belong to `infra.logger` and to
the official artifacts, not here.
"""

import dataclasses

import pytest

from mars777_police.app.state_machine import (
    IllegalTransitionError,
    ProtocolMachine,
    ProtocolPhase,
    TransitionEvidence,
    TransitionResult,
)

P = ProtocolPhase
FORBIDDEN = [
    "timestamp",
    "time",
    "created_at",
    "event_id",
    "uuid",
    "sequence",
    "seq",
    "index",
    "reason",
    "cause",
    "step",
    "completed_steps",
    "turn_number",
    "sub_game",
    "sub_game_index",
    "series_index",
    "cursor",
    "board",
    "truth",
    "move",
    "barrier",
    "score",
    "scent",
    "hash",
    "digest",
    "nonce",
    "signature",
    "payload",
    "json",
    "is_fault",
    "is_absorbing",
    "is_terminal",
    "transition_name",
    "role",
]


def _edges() -> list[tuple[ProtocolPhase, ProtocolPhase]]:
    return [(s, t) for s in ProtocolPhase for t in ProtocolMachine(s).allowed_next()]


def test_evidence_carries_exactly_the_two_phases() -> None:
    names = tuple(f.name for f in dataclasses.fields(TransitionEvidence))
    assert names == ("source_phase", "target_phase")


def test_evidence_has_no_extra_field() -> None:
    names = {f.name for f in dataclasses.fields(TransitionEvidence)}
    for forbidden in FORBIDDEN:
        assert forbidden not in names


def test_evidence_is_frozen_slotted_and_value_equal() -> None:
    evidence = TransitionEvidence(P.BOOT, P.STEP0_NEGOTIATION)
    with pytest.raises(dataclasses.FrozenInstanceError):
        evidence.source_phase = P.READY  # type: ignore[misc]
    assert not hasattr(evidence, "__dict__")
    assert TransitionEvidence.__slots__ == ("source_phase", "target_phase")
    assert evidence == TransitionEvidence(P.BOOT, P.STEP0_NEGOTIATION)
    assert evidence != TransitionEvidence(P.BOOT, P.FAILED)


@pytest.mark.parametrize("value", ["BOOT", None, 0, ProtocolPhase])
def test_evidence_rejects_non_phase_values(value: object) -> None:
    with pytest.raises(IllegalTransitionError):
        TransitionEvidence(value, P.BOOT)  # type: ignore[arg-type]
    with pytest.raises(IllegalTransitionError):
        TransitionEvidence(P.BOOT, value)  # type: ignore[arg-type]


def test_result_carries_only_the_machine_and_its_evidence() -> None:
    names = tuple(f.name for f in dataclasses.fields(TransitionResult))
    assert names == ("machine", "evidence")
    for forbidden in FORBIDDEN:
        assert forbidden not in set(names)


def test_result_is_frozen_and_slotted() -> None:
    result = ProtocolMachine(P.BOOT).advance(P.STEP0_NEGOTIATION)
    with pytest.raises(dataclasses.FrozenInstanceError):
        result.machine = ProtocolMachine(P.FAILED)  # type: ignore[misc]
    assert not hasattr(result, "__dict__")
