"""The per-sub-game log, built from what the reference wire actually sealed.

The counted log builder renders `SealedTurnRecord`s, whose digests come from a
different commitment construction than the one our opponent has verified across
three rehearsals. Rendering those into an official record would put values in it
that no opponent ever saw. These tests pin the alternative: the log carries the
KIT commitments that genuinely crossed the wire, in the same log shape, with
enough beside each one to recompute it.
"""

import pytest

from mars777_police.app.kit_log_document import kit_finalized_log
from mars777_police.app.kit_log_events import SEALED, kit_entry
from mars777_police.app.kit_messages import KitAuditReveal, KitRecord, KitResultClaim, KitRole
from mars777_police.app.kit_payload import PeerPayload, kit_payload
from mars777_police.app.protocol_errors import LocalDefectError
from mars777_police.app.protocol_values import Sha256Digest
from mars777_police.app.sealed_record_values import ActorRole, Intent
from mars777_police.app.turn_cursor import TurnCursor
from mars777_police.domain.actions import MoveAction
from mars777_police.domain.board import Position
from mars777_police.domain.rules import Move
from mars777_police.protocol.commitment_codec import CommitmentCodec, commitment_for

GAME_ID = "MaRs-777-vs-s82kma9e"
GAME_UID = "43994252-2e4d-2b5c-9baa-4bf7aef5b5d6"
CONFIG = "a" * 64
CODEC = CommitmentCodec.KIT_CORE_COMMITMENT_V1


def record(step: int, role: ActorRole, nonce: str) -> KitRecord:
    payload = kit_payload(
        cursor=TurnCursor(1, step),
        role=role,
        action=MoveAction(Move.STAY),
        intent=Intent.TRUTH,
        hint=f"step {step}",
        own_position=Position(step, 0),
        barriers=(),
    )
    return KitRecord(
        PeerPayload(payload), nonce, Sha256Digest(commitment_for(CODEC, payload, nonce))
    )


def ours(count: int = 2) -> tuple[KitRecord, ...]:
    return tuple(record(n, ActorRole.POLICE, f"{n:032x}") for n in range(1, count + 1))


def theirs(count: int = 2) -> KitAuditReveal:
    records = tuple(record(n, ActorRole.THIEF, f"{n + 90:032x}") for n in range(1, count + 1))
    return KitAuditReveal(KitRole.THIEF, records, KitResultClaim.SURVIVAL)


def log(**changes: object) -> dict[str, object]:
    members: dict[str, object] = {
        "game_id": GAME_ID,
        "game_uid": GAME_UID,
        "sub_game": 1,
        "config_sha256": CONFIG,
        "ours": ours(),
        "disclosure": theirs(),
        "peer_verified": True,
        "result": "survival",
        **changes,
    }
    return dict(kit_finalized_log(**members))  # type: ignore[arg-type]


def test_the_log_carries_both_chains_interleaved_by_step() -> None:
    entries = log()["entries"]
    assert isinstance(entries, list)
    assert [entry["phase"] for entry in entries] == ["commit", "reveal"] * 4


def test_every_commitment_can_be_recomputed_from_what_sits_beside_it() -> None:
    """The property that makes this a record rather than an assertion."""
    entries = log()["entries"]
    assert isinstance(entries, list)
    for reveal in [entry for entry in entries if entry["phase"] == "reveal"]:
        payload = {
            "step": reveal["step"],
            "sub_game": reveal["sub_game"],
            "role": reveal["role"],
            "move": reveal["move"],
            "intent": reveal["intent"],
            "hint": reveal["hint"],
            "position": reveal["state"]["self_pos"],  # type: ignore[index]
            "barriers": reveal["state"]["barriers"],  # type: ignore[index]
        }
        assert commitment_for(CODEC, payload, str(reveal["nonce"])) == reveal["commit"], (
            "the log must carry enough beside each commitment to recompute it"
        )


def test_our_own_turns_are_never_marked_verified_by_us() -> None:
    """The peer audits our chain; claiming a verdict on it would be self-issued."""
    entries = log()["entries"]
    assert isinstance(entries, list)
    police = [e for e in entries if e["role"] == "police" and e["phase"] == "commit"]
    assert police and all(entry["verified"] is None for entry in police)


def test_the_peer_turns_carry_the_verdict_we_actually_reached() -> None:
    for verdict in (True, False):
        entries = log(peer_verified=verdict)["entries"]
        assert isinstance(entries, list)
        thief = [e for e in entries if e["role"] == "thief" and e["phase"] == "commit"]
        assert thief and all(entry["verified"] is verdict for entry in thief)


def test_the_state_block_omits_what_the_kit_commitment_does_not_seal() -> None:
    """A state carrying `config_sha256` would not reproduce the digest beside it."""
    entry = kit_entry(ours()[0])
    state = entry["state"]
    assert isinstance(state, dict)
    assert "config_sha256" not in state
    assert set(state) == {"self_pos", "barriers", "step", "role"}


def test_the_entry_renders_exactly_the_sealed_members() -> None:
    entry = kit_entry(ours()[0])
    assert set(entry) == {*SEALED, "commit", "state"} - {"position", "barriers"}


def test_a_sub_game_with_no_disclosure_is_refused() -> None:
    """No audit means no finalized log - not a log that claims one happened."""
    with pytest.raises(LocalDefectError, match="only after this sub-game was audited"):
        log(disclosure=None)


def test_the_audit_block_reports_both_chain_lengths() -> None:
    audit = log()["audit"]
    assert isinstance(audit, dict)
    assert audit["our_records"] == 2 and audit["peer_records"] == 2
    assert audit["result"] == "survival"
