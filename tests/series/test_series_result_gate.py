"""The gate `require_audit` was written for, finally connected.

`ResultAgreementRuntime.require_audit` has existed since Stage 4E-R15 with no
production caller. These tests are the path Stage 5-R4's runner will use:
completed series gate → existing prerequisite → existing result cadence.
"""

import cadence_ops
import pytest
import series_builders as build
from r16_builders import GROUP_A

from mars777_police.app.protocol_errors import StaleMessageError
from mars777_police.app.protocol_values import FinalAuditVerdict
from mars777_police.app.series_audit_gate import SeriesAuditGate


def gate_of(order: tuple[int, ...], tampered: int = 0) -> SeriesAuditGate:
    gate = SeriesAuditGate()
    for audit in build.series(order, tampered=tampered):
        gate.record(audit)
    return gate


def exchange() -> object:
    """The real production `ResultExchange` for our side."""
    return cadence_ops.exchange_for(GROUP_A, 200)


def test_the_existing_prerequisite_accepts_a_verified_series() -> None:
    exchange().require_series_audit(gate_of((1, 2, 3, 4, 5, 6)))


def test_a_tampered_series_cannot_reach_result_agreement() -> None:
    with pytest.raises(StaleMessageError, match="FINAL_AUDIT"):
        exchange().require_series_audit(gate_of((1, 2, 3, 4, 5, 6), tampered=4))


@pytest.mark.parametrize("recorded", [0, 1, 5])
def test_an_incomplete_series_cannot_reach_result_agreement(recorded: int) -> None:
    """`None` is refused by the same check that refuses TAMPERED."""
    gate = gate_of(tuple(range(1, recorded + 1)))
    assert gate.verdict is None
    with pytest.raises(StaleMessageError, match="FINAL_AUDIT"):
        exchange().require_series_audit(gate)


def test_the_prerequisite_only_carries_the_verdict_to_the_runtime() -> None:
    """It stores nothing and decides nothing; the runtime owns the meaning."""
    live = exchange()
    before = (live.local_digest, live.peer_digest, live.own_request_sent, live.verified)
    live.require_series_audit(gate_of((1, 2, 3, 4, 5, 6)))
    assert (live.local_digest, live.peer_digest, live.own_request_sent, live.verified) == before


def test_the_runtime_gate_semantics_are_unchanged() -> None:
    """Exactly the three cases `require_audit` already distinguished."""
    runtime = exchange().runtime
    runtime.require_audit(FinalAuditVerdict.VERIFIED_OK)
    for refused in (None, FinalAuditVerdict.TAMPERED):
        with pytest.raises(StaleMessageError, match="FINAL_AUDIT"):
            runtime.require_audit(refused)


def test_the_full_future_runner_path_is_legal_today() -> None:
    """Six real audits → gate → ResultExchange prerequisite → cadence untouched."""
    gate, live = gate_of((3, 1, 6, 2, 5, 4)), exchange()
    assert gate.verdict is FinalAuditVerdict.VERIFIED_OK
    live.require_series_audit(gate)
    assert live.runtime.is_proposer in (True, False)
    assert not live.own_request_sent
