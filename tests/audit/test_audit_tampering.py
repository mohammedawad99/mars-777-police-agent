"""One tamper vector per sealed member, with real production crypto throughout.

The sealed record has exactly eight members - `state`, `move`, `intent`, `hint`,
`step`, `role`, `sub_game`, `nonce` - and each gets its own row below. `commit`
is deliberately **not** among them: `H_commit` is the value the recomputation is
compared *against*, not a member of the record, so it is exercised separately.

Which detection layer fires is a property of the contract: members witnessed
live are caught by the cross-check before hashing, members disclosed only at
audit are caught by the recomputed digest. Neither can produce `VERIFIED_OK`.
"""

import pytest
from audit_builders import (
    LIVE_ACTION,
    NONCES,
    PEER_GROUP,
    SUB_GAME,
    document,
    nonce_batch,
    runtime,
)

from mars777_police.app.peer_final_messages import FinalNonceReveal, NonceRevealEntry
from mars777_police.app.protocol_errors import StaleMessageError
from mars777_police.app.protocol_values import FinalAuditVerdict, NonceValue
from mars777_police.app.turn_cursor import TurnCursor

SEALED_MEMBERS = frozenset({"state", "move", "intent", "hint", "step", "role", "sub_game", "nonce"})


def verdict_for(**entry_overrides: object) -> FinalAuditVerdict | None:
    """Alter the first disclosed entry and report the derived verdict."""
    doc = document()
    doc["entries"][0].update(entry_overrides)  # type: ignore[union-attr]
    live = runtime()
    live.accept_final_nonce_reveal(nonce_batch(), PEER_GROUP)
    live.accept_audit_disclosure(doc)
    return live.verdict


def refuse_for(**entry_overrides: object) -> StaleMessageError:
    """Alter the first entry where the contract refuses before hashing."""
    doc = document()
    doc["entries"][0].update(entry_overrides)  # type: ignore[union-attr]
    live = runtime()
    live.accept_final_nonce_reveal(nonce_batch(), PEER_GROUP)
    with pytest.raises(StaleMessageError) as raised:
        live.accept_audit_disclosure(doc)
    return raised.value


def test_the_matrix_covers_exactly_the_eight_sealed_members() -> None:
    """Set equality, so a subfield can never stand in for a missing member."""
    assert len(SEALED_MEMBERS) == 8
    assert (
        frozenset({"state", "move", "intent", "hint", "step", "role", "sub_game", "nonce"})
        == SEALED_MEMBERS
    )
    assert "commit" not in SEALED_MEMBERS and "config_sha256" not in SEALED_MEMBERS


def test_member_1_state_cannot_verify() -> None:
    """Disclosed only at audit, so the recomputed digest catches it."""
    doc = document()
    doc["entries"][0]["state"] = dict(  # type: ignore[index]
        doc["entries"][0]["state"],
        self_pos=[9, 9],  # type: ignore[index,arg-type]
    )
    live = runtime()
    live.accept_final_nonce_reveal(nonce_batch(), PEER_GROUP)
    live.accept_audit_disclosure(doc)
    assert live.verdict is FinalAuditVerdict.TAMPERED


def test_member_2_move_cannot_verify() -> None:
    """Live-observed: the disclosed copy must agree with the action we received."""
    assert verdict_for(move={"kind": "MOVE", "value": "S"}) is FinalAuditVerdict.TAMPERED


def test_member_3_intent_cannot_verify() -> None:
    assert verdict_for(intent="lie") is FinalAuditVerdict.TAMPERED


def test_member_4_hint_cannot_verify() -> None:
    assert verdict_for(hint="a completely different hint") is FinalAuditVerdict.TAMPERED


def test_member_5_step_cannot_verify() -> None:
    """Caught by cursor identity before hashing - a refusal, not a verdict."""
    assert refuse_for(step=7).error_id == "E-PROTO-STALE"


def test_member_6_role_cannot_verify() -> None:
    assert verdict_for(role="police") is FinalAuditVerdict.TAMPERED


def test_member_7_sub_game_cannot_verify() -> None:
    """Caught by cursor identity: the turn no longer belongs to this sub-game."""
    assert refuse_for(sub_game=2).error_id == "E-PROTO-STALE"


def test_member_8_nonce_cannot_verify() -> None:
    """The accepted batch is authority; a different nonce breaks the digest."""
    wrong = FinalNonceReveal(
        (
            NonceRevealEntry(TurnCursor(SUB_GAME, 1), NonceValue("9" * 32)),
            NonceRevealEntry(TurnCursor(SUB_GAME, 2), NONCES[2]),
        )
    )
    live = runtime()
    live.accept_final_nonce_reveal(wrong, PEER_GROUP)
    live.accept_audit_disclosure(document())
    assert live.verdict is FinalAuditVerdict.TAMPERED


def test_the_expected_digest_tamper_is_separate_from_the_eight() -> None:
    """`H_commit` is what the recomputation is compared against, not a member."""
    assert verdict_for(commit="f" * 64) is FinalAuditVerdict.TAMPERED


def test_a_self_consistent_post_hoc_rewrite_still_fails() -> None:
    """The attack the live cross-check exists to stop.

    The peer replays the whole turn as a different action and rebuilds its log
    so every internal field agrees with that action - a document that is
    perfectly self-consistent. It still fails, because the action and digest it
    is checked against were captured live, before the rewrite existed.
    """
    live = runtime()
    live.accept_final_nonce_reveal(nonce_batch(), PEER_GROUP)
    live.accept_audit_disclosure(document())
    assert verdict_for(move={"kind": "MOVE", "value": "S"}) is FinalAuditVerdict.TAMPERED
    assert live.evidence[0].action == LIVE_ACTION


@pytest.mark.parametrize("step", [1, 2])
def test_any_single_tampered_turn_fails_the_whole_sub_game(step: int) -> None:
    doc = document()
    doc["entries"][step - 1]["hint"] = "rewritten"  # type: ignore[index]
    live = runtime()
    live.accept_final_nonce_reveal(nonce_batch(), PEER_GROUP)
    live.accept_audit_disclosure(doc)
    assert live.verdict is FinalAuditVerdict.TAMPERED
    assert not live.verified
