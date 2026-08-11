"""What this seam must not have touched.

The series verdict is a local prerequisite, not a new fact about the game - so
nothing peer-visible and nothing hashed may have moved.
"""

import dataclasses

from r16_source import imports_of, tokens_of

from mars777_police.app import peer_messages
from mars777_police.app import series_audit_gate as gate
from mars777_police.app.peer_final_messages import ResultAgreement
from mars777_police.app.protocol_values import FinalAuditVerdict
from mars777_police.app.result_core_runtime import SubGameOutcomeLine
from mars777_police.app.result_core_values import CumulativeResult
from mars777_police.app.result_values import ResultContribution, ResultContributionEntry
from mars777_police.transport.server import PEER_TOOLS


def names(value: type) -> set[str]:
    """The declared field names of a dataclass."""
    return {field.name for field in dataclasses.fields(value)}


def test_the_verdict_vocabulary_is_still_exactly_two_words() -> None:
    assert {member.value for member in FinalAuditVerdict} == {"Verified OK", "TAMPERED"}
    assert len(FinalAuditVerdict) == 2


def test_no_audit_verdict_became_a_peer_message() -> None:
    for invented in ("SeriesAudit", "SeriesAuditVerdict", "FinalAudit", "AuditAck"):
        assert invented not in dir(peer_messages)
    assert not hasattr(peer_messages, "FinalAuditVerdict")


def test_no_result_hashed_value_gained_an_audit_field() -> None:
    """The prerequisite is a gate, never another hashed member."""
    assert names(ResultAgreement) == {
        "game_id",
        "game_uid",
        "declaration_ref",
        "timestamp",
        "contribution",
    }
    assert names(ResultContribution) == {"group_id", "entries"}
    assert names(ResultContributionEntry) == {"sub_game", "github_commit", "tokens"}
    assert names(SubGameOutcomeLine) == {"sub_game", "cop_score", "thief_score", "outcome"}
    assert names(CumulativeResult) == {"cop_total", "thief_total", "series_outcome"}


def test_the_approval_core_declares_no_audit_member() -> None:
    """The hashed core is a value type; an audit field would have to appear here."""
    from mars777_police.app.result_core_values import ResultApprovalCore

    members = names(ResultApprovalCore)
    for invented in ("audit", "audit_result", "verdict", "series_audit", "verified"):
        assert invented not in members


def test_the_gate_touches_no_transport_infra_or_framework() -> None:
    assert all("transport" not in name and "infra" not in name for name in imports_of(gate))
    for forbidden in ("fastmcp", "httpx", "ngrok", "environ", "getenv", "socket", "open", "Path"):
        assert forbidden not in tokens_of(gate)


def test_the_gate_implements_no_cryptography():
    for forbidden in ("hashlib", "sha256", "secrets", "compute_commitment", "dumps"):
        assert forbidden not in tokens_of(gate)


def test_the_four_tools_are_unchanged() -> None:
    assert sorted(PEER_TOOLS) == ["negotiate", "receive_control", "receive_turn", "submit_audit"]
