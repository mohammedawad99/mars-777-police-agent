"""Six sub-games, one verdict, and the ways it must refuse to be reached."""

import dataclasses

import pytest
import series_builders as build

from mars777_police.app.audit_values import AuditOutcome, AuditPhase
from mars777_police.app.protocol_errors import LocalDefectError, StaleMessageError
from mars777_police.app.protocol_values import FinalAuditVerdict
from mars777_police.app.series_audit_gate import REQUIRED_SUB_GAMES, SeriesAuditGate


def gate_of(order: tuple[int, ...], tampered: int = 0) -> SeriesAuditGate:
    """Record real audits for *order*, in that order."""
    gate = SeriesAuditGate()
    for audit in build.series(order, tampered=tampered):
        gate.record(audit)
    return gate


def test_the_required_set_is_exactly_the_six_a_contribution_covers() -> None:
    """One source of six: the sequence the result contribution already fixes."""
    from mars777_police.app.result_values import SUB_GAME_SEQUENCE

    assert REQUIRED_SUB_GAMES == frozenset(SUB_GAME_SEQUENCE) == {1, 2, 3, 4, 5, 6}


def test_a_fresh_gate_has_no_verdict() -> None:
    gate = SeriesAuditGate()
    assert gate.verdict is None and not gate.complete and gate.audited == ()


@pytest.mark.parametrize("recorded", [1, 2, 3, 4, 5])
def test_an_incomplete_series_never_yields_a_verdict(recorded: int) -> None:
    """Five verified and one missing is not `VERIFIED_OK` - it is nothing."""
    gate = gate_of(tuple(range(1, recorded + 1)))
    assert gate.verdict is None
    assert not gate.complete
    assert len(gate.audited) == recorded


def test_all_six_verified_gives_a_verified_series() -> None:
    assert gate_of((1, 2, 3, 4, 5, 6)).verdict is FinalAuditVerdict.VERIFIED_OK


@pytest.mark.parametrize("tampered", [1, 3, 6])
def test_one_tampered_sub_game_taints_the_completed_series(tampered: int) -> None:
    gate = gate_of((1, 2, 3, 4, 5, 6), tampered=tampered)
    assert gate.complete
    assert gate.verdict is FinalAuditVerdict.TAMPERED


def test_a_tampered_sub_game_before_completion_still_yields_no_verdict() -> None:
    """The result gate stays closed; TAMPERED only lands once the six are in."""
    gate = gate_of((1, 2), tampered=2)
    assert gate.verdict is None and not gate.complete


def test_recording_order_does_not_change_the_verdict() -> None:
    forward = gate_of((1, 2, 3, 4, 5, 6))
    backward = gate_of((6, 5, 4, 3, 2, 1))
    shuffled = gate_of((6, 2, 1, 5, 4, 3))
    assert forward.verdict is backward.verdict is shuffled.verdict
    assert forward.audited == backward.audited == shuffled.audited == (1, 2, 3, 4, 5, 6)


def test_the_same_sub_game_cannot_be_recorded_twice() -> None:
    gate = SeriesAuditGate()
    gate.record(build.audit_of(1))
    with pytest.raises(LocalDefectError, match="already audited"):
        gate.record(build.audit_of(1))


def test_a_sub_game_outside_the_series_is_refused() -> None:
    gate = SeriesAuditGate()
    with pytest.raises(LocalDefectError, match="not part of this series"):
        gate.record(build.empty_audit_of(7))


def test_an_unfinished_audit_cannot_be_recorded() -> None:
    """An audit that has decided nothing must not count toward a finished series."""
    import audit_builders

    gate = SeriesAuditGate()
    live = audit_builders.runtime()
    assert live.phase is not AuditPhase.COMPLETE
    with pytest.raises(StaleMessageError, match="only a completed"):
        gate.record(live)


def test_the_gate_keeps_the_outcome_and_not_the_runtime() -> None:
    """Frozen snapshots: asking the runtime again later cannot change history."""
    gate = SeriesAuditGate()
    audit = build.audit_of(1)
    gate.record(audit)
    held = gate.outcomes[1]
    assert type(held) is AuditOutcome
    assert held is audit.outcome
    assert dataclasses.is_dataclass(held) and held.__dataclass_params__.frozen
    assert all(not isinstance(value, type(audit)) for value in gate.outcomes.values())
