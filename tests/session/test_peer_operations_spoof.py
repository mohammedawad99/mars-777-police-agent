"""The guards that were `x != x` until the session existed.

Before Stage 5-R3R the only available sender was the payload's own claim, which
made `sender_id != request.contribution.group_id` permanently false. These tests
give the adapter an authenticated identity that **disagrees** with the payload
and require the real application refusal - which is only possible now.
"""

import pytest
import session_builders as build
from peer_ops import agreement, final_nonce, proposal
from r16_builders import GROUP_B

from mars777_police.app.protocol_errors import ReportDisagreeError, StaleMessageError


def test_a_result_request_contributing_another_group_is_refused() -> None:
    """`E-REPORT-DISAGREE`: the authenticated sender does not own the payload."""
    with pytest.raises(ReportDisagreeError) as raised:
        build.operations().on_result_agreement(agreement(), build.bound("GROUP-IMPOSTOR"))
    assert raised.value.error_id == "E-REPORT-DISAGREE"


def test_a_matching_authenticated_sender_completes_the_result_request() -> None:
    digest = build.operations().on_result_agreement(agreement(), build.bound(GROUP_B))
    assert len(digest.value) == 64


def test_the_result_guard_is_not_tautological() -> None:
    """The same payload passes or fails purely on the session identity."""
    payload = agreement()
    assert payload.contribution.group_id == GROUP_B
    build.operations().on_result_agreement(payload, build.bound(GROUP_B))
    with pytest.raises(ReportDisagreeError):
        build.operations().on_result_agreement(payload, build.bound("GROUP-IMPOSTOR"))


def test_a_config_proposal_from_a_non_participant_session_is_refused() -> None:
    with pytest.raises(StaleMessageError, match="not a party"):
        build.operations().on_config_proposal(proposal(), build.bound("GROUP-INTRUDER"))


def test_the_config_guard_is_not_tautological() -> None:
    """The identical proposal is accepted for one session and refused for another."""
    build.operations().on_config_proposal(proposal(), build.bound(GROUP_B))
    with pytest.raises(StaleMessageError):
        build.operations().on_config_proposal(proposal(), build.bound("GROUP-INTRUDER"))


def test_a_nonce_batch_from_the_wrong_authenticated_sender_is_refused() -> None:
    """`AuditRuntime` compares the session sender with its own peer, never itself."""
    import audit_builders

    live = build.operations(audit=audit_builders.runtime())
    with pytest.raises(StaleMessageError, match="expected peer"):
        live.on_final_nonce_reveal(final_nonce(), build.bound("GROUP-IMPOSTOR"))


def test_the_audit_guard_accepts_only_the_runtimes_expected_peer() -> None:
    import audit_builders

    live = build.operations(audit=audit_builders.runtime())
    live.on_final_nonce_reveal(audit_builders.nonce_batch(), build.bound(audit_builders.PEER_GROUP))
