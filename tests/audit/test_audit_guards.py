"""Ownership, boundaries and the things this runtime deliberately does not do.

No peer-visible verdict family, no sanction, no result work, no transport, and
no second copy of the hash - the digest comes from the same production primitive
the live producer used, reached through the registered `CommitmentPort` seam.
"""

import pytest
from audit_builders import CONFIG, PEER, PEER_GROUP, context, evidence, runtime
from r16_source import imports_of, tokens_of

from mars777_police.app import audit_disclosure as disclosure
from mars777_police.app import audit_runtime as module
from mars777_police.app import peer_messages
from mars777_police.app.audit_runtime import AuditRuntime
from mars777_police.app.audit_values import AuditOutcome, SubGameContext
from mars777_police.app.ports import CommitmentPort
from mars777_police.app.protocol_values import FinalAuditVerdict
from mars777_police.app.turn_cursor import TurnCursor
from mars777_police.app.turn_protocol_state import TurnEvidence
from mars777_police.domain.actions import MoveAction
from mars777_police.domain.rules import Move
from mars777_police.protocol.audit_commitment import CommitmentRecomputer
from mars777_police.transport.server import PEER_TOOLS


def test_the_runtime_computes_no_hash_of_its_own() -> None:
    tokens = tokens_of(module)
    for forbidden in ("hashlib", "sha256", "compute_commitment", "json", "dumps"):
        assert forbidden not in tokens


def test_the_runtime_reaches_crypto_only_through_the_registered_port() -> None:
    """`app` never imports `protocol`; the seam is `CommitmentPort`."""
    imported = imports_of(module)
    assert all("protocol." not in name for name in imported)
    assert all("transport" not in name and not name.startswith("infra") for name in imported)
    assert "CommitmentPort" in tokens_of(module)


def test_the_commitment_port_keeps_exactly_its_two_frozen_operations() -> None:
    """`API_BOUNDARIES.md` freezes sealed fields in, digest and comparison out.

    An action-to-JSON projection and a coordinate constructor are different
    responsibilities: both are reachable inward from `app` already, so neither
    may be smuggled onto the cryptographic seam.
    """
    declared = {name for name in vars(CommitmentPort) if not name.startswith("_")}
    assert declared == {"recompute", "matches"}
    for widened in ("action_value", "position", "canonical_action_value"):
        assert not hasattr(CommitmentRecomputer, widened)
        assert widened not in tokens_of(module)


def test_the_disclosure_reader_parses_inward_and_never_outward() -> None:
    """It reaches `domain` constructors directly, not `protocol` through a port."""
    imported = imports_of(disclosure)
    assert all("protocol." not in name and "transport" not in name for name in imported)
    assert {"MoveAction", "BarrierAction", "Position", "Move"} <= tokens_of(disclosure)


def test_the_runtime_touches_no_environment_network_or_secret() -> None:
    tokens = tokens_of(module)
    for forbidden in ("os", "environ", "getenv", "socket", "urllib", "open", "Path"):
        assert forbidden not in tokens


def test_no_peer_visible_final_audit_family_exists() -> None:
    exported = dir(peer_messages)
    for invented in ("FinalAudit", "FinalAuditRequest", "AuditVerdictMessage", "AuditAck"):
        assert invented not in exported


def test_the_public_tool_and_kind_vocabulary_is_unchanged() -> None:
    assert sorted(PEER_TOOLS) == ["negotiate", "receive_control", "receive_turn", "submit_audit"]


def test_the_verdict_is_local_and_never_a_message() -> None:
    """`FinalAuditVerdict` is audit/log/replay vocabulary, not a peer family."""
    assert not hasattr(peer_messages, "FinalAuditVerdict")
    assert set(FinalAuditVerdict) == {FinalAuditVerdict.VERIFIED_OK, FinalAuditVerdict.TAMPERED}


def test_the_runtime_refuses_a_duplicated_evidence_cursor() -> None:
    doubled = evidence((1,)) + evidence((1,))
    with pytest.raises(ValueError, match="duplicate cursor"):
        AuditRuntime(context(), doubled, CommitmentRecomputer())


def test_the_runtime_refuses_evidence_from_another_sub_game() -> None:
    foreign = (TurnEvidence(TurnCursor(2, 1), CONFIG, MoveAction(Move.N), "x", True),)
    with pytest.raises(ValueError, match="belong to this sub-game"):
        AuditRuntime(context(), foreign, CommitmentRecomputer())


def test_an_outcome_cannot_claim_both_verified_and_a_tampered_step() -> None:
    with pytest.raises(ValueError, match="names no tampered step"):
        AuditOutcome(FinalAuditVerdict.VERIFIED_OK, 1)
    with pytest.raises(ValueError, match="must name the first failing step"):
        AuditOutcome(FinalAuditVerdict.TAMPERED)


def test_the_context_refuses_impossible_identity() -> None:
    with pytest.raises(ValueError, match="sub_game"):
        SubGameContext("g", "u", 0, CONFIG, PEER, PEER_GROUP)
    with pytest.raises(ValueError, match="non-empty"):
        SubGameContext("", "u", 1, CONFIG, PEER, PEER_GROUP)


def test_the_expected_cursor_set_is_ordered_by_step() -> None:
    assert [cursor.step for cursor in runtime().expected] == [1, 2]


def test_no_verdict_exists_before_the_audit_completes() -> None:
    live = runtime()
    assert live.verdict is None and not live.verified
    assert live.outcome is None
