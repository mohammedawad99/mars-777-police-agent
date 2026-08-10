"""The two-request cadence: order, timestamp immutability, and both gates.

Both participant orders are exercised, because the proposer follows the
byte-wise lower `group_id` **value** and not the `group_a` slot - and in this
fixture those two disagree.
"""

import pytest
from r16_builders import (
    COMMIT_A,
    COMMIT_B,
    DECLARATION_REF,
    GAME_ID,
    GAME_UID,
    GROUP_A,
    GROUP_B,
    PARTICIPANTS,
    STAMP,
    FixedClock,
    contribution,
)

from mars777_police.app.artifact_values import UtcTimestamp
from mars777_police.app.peer_final_messages import ResultAgreement
from mars777_police.app.protocol_errors import ReportDisagreeError, StaleMessageError
from mars777_police.app.protocol_values import FinalAuditVerdict
from mars777_police.app.result_agreement_runtime import ResultAgreementRuntime, timestamp_proposer
from mars777_police.app.result_identity_values import ResultParticipants

OTHER = UtcTimestamp("2026-08-07T02:00:00Z")


def runtime(group_id: str, participants: ResultParticipants = PARTICIPANTS) -> object:
    return ResultAgreementRuntime(group_id, GAME_ID, GAME_UID, participants, FixedClock())


def test_the_proposer_is_the_byte_wise_lower_group_id_not_the_group_a_slot() -> None:
    assert timestamp_proposer(PARTICIPANTS) == GROUP_B
    assert PARTICIPANTS.group_a == GROUP_A
    assert runtime(GROUP_B).is_proposer
    assert not runtime(GROUP_A).is_proposer


def test_the_rule_follows_the_value_when_the_slots_are_swapped() -> None:
    swapped = ResultParticipants(GROUP_B, GROUP_A)
    assert timestamp_proposer(swapped) == GROUP_B
    assert runtime(GROUP_B, swapped).is_proposer


def test_only_the_proposer_may_open_the_agreement() -> None:
    first = runtime(GROUP_B).open_agreement(contribution(GROUP_B, COMMIT_B))
    assert first.timestamp == STAMP
    assert first.declaration_ref == DECLARATION_REF
    with pytest.raises(StaleMessageError):
        runtime(GROUP_A).open_agreement(contribution(GROUP_A, COMMIT_A))


def test_the_request_carries_no_digest_and_no_acceptance_flag() -> None:
    first = runtime(GROUP_B).open_agreement(contribution(GROUP_B, COMMIT_B))
    for absent in ("result_sha256", "accepted", "ok", "mutual_agreement", "reported_by"):
        assert not hasattr(first, absent)


def test_the_non_proposer_adopts_the_timestamp_verbatim_and_echoes_it() -> None:
    first = runtime(GROUP_B).open_agreement(contribution(GROUP_B, COMMIT_B))
    adopted = runtime(GROUP_A).accept(first, GROUP_B)
    assert adopted == STAMP
    second = runtime(GROUP_A).request(adopted, contribution(GROUP_A, COMMIT_A))
    assert second.timestamp == STAMP
    assert runtime(GROUP_B).accept(second, GROUP_A, proposed=STAMP) == STAMP


def test_regenerating_our_request_never_regenerates_the_timestamp() -> None:
    non_proposer = runtime(GROUP_A)
    contributed = contribution(GROUP_A, COMMIT_A)
    first = non_proposer.request(STAMP, contributed)
    assert non_proposer.request(STAMP, contributed) == first


def test_an_echoed_timestamp_that_differs_is_a_disagreement() -> None:
    second = runtime(GROUP_A).request(OTHER, contribution(GROUP_A, COMMIT_A))
    with pytest.raises(ReportDisagreeError) as failure:
        runtime(GROUP_B).accept(second, GROUP_A, proposed=STAMP)
    assert failure.value.error_id == "E-REPORT-DISAGREE"


def test_the_non_proposer_may_not_send_the_first_request() -> None:
    early = runtime(GROUP_A).request(STAMP, contribution(GROUP_A, COMMIT_A))
    with pytest.raises(StaleMessageError):
        runtime(GROUP_B).accept(early, GROUP_A)


def test_a_second_request_from_the_same_peer_is_stale() -> None:
    first = runtime(GROUP_B).open_agreement(contribution(GROUP_B, COMMIT_B))
    with pytest.raises(StaleMessageError):
        runtime(GROUP_A).accept(first, GROUP_B, seen=True)


def test_a_request_from_ourselves_is_stale() -> None:
    first = runtime(GROUP_B).open_agreement(contribution(GROUP_B, COMMIT_B))
    with pytest.raises(StaleMessageError):
        runtime(GROUP_B).accept(first, GROUP_B)


def test_we_refuse_to_contribute_another_participants_data() -> None:
    with pytest.raises(ReportDisagreeError):
        runtime(GROUP_A).request(STAMP, contribution(GROUP_B, COMMIT_B))


def test_an_inbound_contribution_must_belong_to_its_authenticated_sender() -> None:
    """Built directly, because our own runtime already refuses to forge one."""
    forged = ResultAgreement(
        GAME_ID, GAME_UID, DECLARATION_REF, STAMP, contribution(GROUP_A, COMMIT_A)
    )
    with pytest.raises(ReportDisagreeError):
        runtime(GROUP_A).accept(forged, GROUP_B)


def test_a_request_naming_another_game_is_a_disagreement() -> None:
    other = ResultAgreementRuntime(GROUP_B, "another-game", GAME_UID, PARTICIPANTS, FixedClock())
    with pytest.raises(ReportDisagreeError):
        runtime(GROUP_A).accept(other.open_agreement(contribution(GROUP_B, COMMIT_B)), GROUP_B)


def test_the_runtime_refuses_to_start_before_the_local_final_audit_passes() -> None:
    for verdict in (None, FinalAuditVerdict.TAMPERED):
        with pytest.raises(StaleMessageError):
            runtime(GROUP_B).require_audit(verdict)
    runtime(GROUP_B).require_audit(FinalAuditVerdict.VERIFIED_OK)


def test_a_mismatched_declaration_reference_is_unconstructable() -> None:
    """Which is why the runtime does not re-check it after matching `game_id`."""
    from mars777_police.app.result_values import InvalidResultValueError

    with pytest.raises(InvalidResultValueError):
        ResultAgreement(
            GAME_ID, GAME_UID, "declaration_other.json", STAMP, contribution(GROUP_B, COMMIT_B)
        )
    assert runtime(GROUP_A).declaration_ref == DECLARATION_REF
