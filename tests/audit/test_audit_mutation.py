"""A caller cannot reach back into an accepted document and change the verdict.

`AuditDocument` is `dict[str, object]` - mutable, and owned by whoever built it.
The runtime therefore derives everything during acceptance and retains no part
of it: only `AuditOutcome`, a frozen value, survives the call. These tests
mutate the original aggressively afterwards and require the derived state to be
byte-identical.
"""

from audit_builders import PEER_GROUP, SUB_GAME, document, nonce_batch, runtime
from test_audit_tampering import verdict_for

from mars777_police.app.protocol_values import FinalAuditVerdict
from mars777_police.app.turn_cursor import TurnCursor


def accepted() -> tuple[object, dict[str, object]]:
    """A completed audit and the caller-owned document it was derived from."""
    doc = document()
    live = runtime()
    live.accept_final_nonce_reveal(nonce_batch(), PEER_GROUP)
    live.accept_audit_disclosure(doc)
    return live, doc


def test_mutating_top_level_identity_afterwards_changes_nothing() -> None:
    live, doc = accepted()
    doc["game_id"] = "some-other-game"
    doc["sub_game"] = 99
    doc["config_sha256"] = "e" * 64
    assert live.verdict is FinalAuditVerdict.VERIFIED_OK
    assert live.verified


def test_mutating_a_nested_entry_afterwards_changes_nothing() -> None:
    live, doc = accepted()
    doc["entries"][0]["commit"] = "0" * 64  # type: ignore[index]
    doc["entries"][0]["move"] = {"kind": "MOVE", "value": "S"}  # type: ignore[index]
    doc["entries"][0]["hint"] = "rewritten after the fact"  # type: ignore[index]
    assert live.verdict is FinalAuditVerdict.VERIFIED_OK


def test_mutating_nested_state_afterwards_changes_nothing() -> None:
    live, doc = accepted()
    doc["entries"][0]["state"]["self_pos"] = [9, 9]  # type: ignore[index]
    doc["entries"][0]["state"]["barriers"].append([4, 4])  # type: ignore[index,union-attr]
    assert live.verdict is FinalAuditVerdict.VERIFIED_OK


def test_emptying_the_entry_list_afterwards_changes_nothing() -> None:
    live, doc = accepted()
    doc["entries"].clear()  # type: ignore[union-attr]
    assert live.verdict is FinalAuditVerdict.VERIFIED_OK
    assert live.outcome is not None and live.outcome.tampered_step is None


def test_the_runtime_retains_no_part_of_the_document() -> None:
    """The only surviving state is the frozen outcome and the semantic nonces."""
    from dataclasses import fields

    live, doc = accepted()
    held = [getattr(live, f.name) for f in fields(live)]
    assert all(value is not doc for value in held)
    assert all(value is not doc["entries"] for value in held)
    assert live.outcome is not None
    assert all(
        not isinstance(getattr(live.outcome, f.name), dict | list) for f in fields(live.outcome)
    )


def test_a_non_action_in_live_evidence_cannot_verify() -> None:
    """`TurnEvidence.action` is typed `object`, so the audit narrows defensively."""
    from audit_builders import context, digest

    from mars777_police.app.audit_runtime import AuditRuntime
    from mars777_police.app.turn_protocol_state import TurnEvidence
    from mars777_police.protocol.audit_commitment import CommitmentRecomputer

    bogus = (
        TurnEvidence(TurnCursor(SUB_GAME, 1), digest(1), "not an action", "moving north", True),
    )
    live = AuditRuntime(context(), bogus, CommitmentRecomputer())
    live.accept_final_nonce_reveal(nonce_batch((1,)), PEER_GROUP)
    live.accept_audit_disclosure(document((1,)))
    assert live.verdict is FinalAuditVerdict.TAMPERED


def test_a_semantically_invalid_disclosed_member_cannot_verify() -> None:
    """A value the domain refuses to construct is a failed audit, not a crash."""
    assert verdict_for(intent="sideways") is FinalAuditVerdict.TAMPERED


def test_an_invalid_disclosed_config_digest_cannot_verify() -> None:
    from audit_builders import entry

    broken = dict(entry(1)["state"], config_sha256="not-a-digest")  # type: ignore[arg-type]
    assert verdict_for(state=broken) is FinalAuditVerdict.TAMPERED
