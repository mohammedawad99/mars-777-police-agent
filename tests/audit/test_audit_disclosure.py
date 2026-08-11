"""The disclosed log: identity binding, completeness, and the verdict we derive.

The recurring theme is that the peer's document is evidence, not authority. Its
identity must match the sub-game we played, its turns must match the turns we
witnessed, and its own verdict fields are not read at all.
"""

import pytest
from audit_builders import (
    CONFIG,
    GAME_ID,
    PEER_GROUP,
    audited,
    document,
    entry,
    nonce_batch,
    runtime,
)

from mars777_police.app.audit_values import AuditPhase
from mars777_police.app.protocol_errors import MalformedMessageError, StaleMessageError
from mars777_police.app.protocol_values import FinalAuditVerdict


def test_a_correct_disclosure_verifies_locally() -> None:
    live = audited()
    assert live.verdict is FinalAuditVerdict.VERIFIED_OK
    assert live.verified
    assert live.outcome is not None and live.outcome.tampered_step is None
    assert live.phase is AuditPhase.COMPLETE


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("game_id", "mars777-vs-someone-else-2026w1-uid9999"),
        ("game_uid", "uid9999"),
        ("sub_game", 2),
        ("config_sha256", "e" * 64),
    ],
)
def test_a_document_for_another_identity_is_refused(field: str, value: object) -> None:
    live = runtime()
    live.accept_final_nonce_reveal(nonce_batch(), PEER_GROUP)
    with pytest.raises(StaleMessageError, match="not this sub-game"):
        live.accept_audit_disclosure(document(**{field: value}))


def test_a_missing_expected_turn_is_refused() -> None:
    live = runtime()
    live.accept_final_nonce_reveal(nonce_batch(), PEER_GROUP)
    with pytest.raises(StaleMessageError, match="played turns"):
        live.accept_audit_disclosure(document((1,)))


def test_an_extra_impossible_turn_is_refused() -> None:
    live = runtime()
    live.accept_final_nonce_reveal(nonce_batch(), PEER_GROUP)
    doc = document()
    doc["entries"] = [*document()["entries"], entry(1) | {"step": 9}]  # type: ignore[misc]
    with pytest.raises(StaleMessageError, match="played turns"):
        live.accept_audit_disclosure(doc)


def test_a_duplicate_turn_association_is_refused() -> None:
    live = runtime()
    live.accept_final_nonce_reveal(nonce_batch(), PEER_GROUP)
    doc = document()
    doc["entries"] = [entry(1), entry(1)]
    with pytest.raises(StaleMessageError, match="repeats a turn"):
        live.accept_audit_disclosure(doc)


def test_a_disclosure_before_the_nonce_batch_is_refused() -> None:
    with pytest.raises(StaleMessageError, match="cannot arrive"):
        runtime().accept_audit_disclosure(document())


def test_a_duplicate_disclosure_is_refused() -> None:
    live = audited()
    with pytest.raises(StaleMessageError, match="cannot arrive"):
        live.accept_audit_disclosure(document())


@pytest.mark.parametrize("broken", [{"entries": "not a list"}, {"game_id": 7}])
def test_a_malformed_document_is_a_protocol_failure_not_a_verdict(broken: dict) -> None:
    """Malformed transport data is `E-PROTO-MALFORMED`, never TAMPERED."""
    live = runtime()
    live.accept_final_nonce_reveal(nonce_batch(), PEER_GROUP)
    with pytest.raises((MalformedMessageError, StaleMessageError)) as raised:
        live.accept_audit_disclosure(document(**broken))
    assert raised.value.error_id in {"E-PROTO-MALFORMED", "E-PROTO-STALE"}


def test_peer_supplied_verdict_annotations_are_ignored() -> None:
    """`audit.result` and `entries[].verified` are LOCAL-DERIVED-AUDIT."""
    hostile = document()
    hostile["audit"] = {"result": "TAMPERED", "tampered_step": 1}
    for item in hostile["entries"]:  # type: ignore[attr-defined]
        item["verified"] = False
    live = runtime()
    live.accept_final_nonce_reveal(nonce_batch(), PEER_GROUP)
    live.accept_audit_disclosure(hostile)
    assert live.verdict is FinalAuditVerdict.VERIFIED_OK


def test_a_peer_claiming_verified_cannot_rescue_a_tampered_log() -> None:
    hostile = document()
    hostile["audit"] = {"result": "Verified OK"}
    hostile["entries"][0]["hint"] = "a different hint"  # type: ignore[index]
    live = runtime()
    live.accept_final_nonce_reveal(nonce_batch(), PEER_GROUP)
    live.accept_audit_disclosure(hostile)
    assert live.verdict is FinalAuditVerdict.TAMPERED


def test_mutating_the_document_after_acceptance_cannot_change_the_verdict() -> None:
    """Nothing nested is retained by reference."""
    doc = document()
    live = audited(doc)
    before = live.verdict
    doc["game_id"] = GAME_ID + "-tampered"
    doc["entries"][0]["commit"] = "0" * 64  # type: ignore[index]
    doc["config_sha256"] = CONFIG.value.replace("d", "e")
    assert live.verdict is before is FinalAuditVerdict.VERIFIED_OK
