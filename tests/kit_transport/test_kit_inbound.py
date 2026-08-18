"""The inbound KIT boundary: the pinned wire in, our typed semantics out.

Every accept and every refusal below is a row of the pinned
`vectors/turn_message.json` at `ad65576`, reproduced in `kit_wire_vectors`. The
kit decides them **before any state change** - an inbound turn is adversarial
input and a partly applied bad turn cannot be rolled back.

The unknown-key row is the one that looks like laxity and is not: it is the
kit's declared extension seam, and a receiver that refuses it cannot be extended
without a flag day. Tolerated is not the same as trusted - the tolerated key
reaches no semantic value at all.
"""

import pytest
from kit_wire_vectors import (
    AUDIT,
    CONTROL,
    CONTROL_KINDS,
    NEGOTIATION,
    RESULT_CLAIMS,
    TURN,
    TURN_REFUSALS,
    TURN_TOLERATED,
    turn,
)
from pydantic import ValidationError

from mars777_police.app.kit_messages import KitControlKind, KitResultClaim, KitRole
from mars777_police.app.protocol_values import Sha256Digest
from mars777_police.transport.codec_kit_pregame import (
    decode_kit_audit,
    decode_kit_control,
    decode_kit_greeting,
)
from mars777_police.transport.codec_kit_turn import decode_kit_turn
from mars777_police.transport.kit_envelopes import (
    KitAuditPayload,
    KitControlMessage,
    KitNegotiateMessage,
    KitTurnMessage,
)


def test_the_pinned_accepted_turn_decodes_to_our_own_semantic_values() -> None:
    value = decode_kit_turn(KitTurnMessage.model_validate(TURN))

    assert value.step == 7
    assert value.sender is KitRole.POLICE
    assert value.hint == "north of the park"
    assert value.commit == Sha256Digest("a" * 64)
    assert value.timestamp == "2026-08-08T19:00:00Z"
    assert value.barrier_placed is not None
    assert (value.barrier_placed.row, value.barrier_placed.col) == (5, 6)
    assert value.capture_claim is None
    assert value.claim_response is None
    assert value.survival_claimed is False


def test_the_smell_grid_is_kept_exactly_as_the_peer_sent_it() -> None:
    """Binary64 in, binary64 out. Converting it here would be a physics claim."""
    value = decode_kit_turn(KitTurnMessage.model_validate(TURN))

    assert dict(value.smell_grid) == {"3,3": 0.9, "3,4": 0.5, "4,3": 0.5}


def test_an_unknown_key_is_tolerated_and_reaches_no_semantic_value() -> None:
    wire = KitTurnMessage.model_validate(TURN | TURN_TOLERATED)

    assert decode_kit_turn(wire) == decode_kit_turn(KitTurnMessage.model_validate(TURN))
    assert not hasattr(wire, "unknown_field")


@pytest.mark.parametrize(("changes", "reason"), TURN_REFUSALS)
def test_every_pinned_refusal_row_is_refused(changes: dict[str, object], reason: str) -> None:
    with pytest.raises(ValidationError):
        KitTurnMessage.model_validate(turn(**changes))


def test_a_missing_required_key_is_never_filled_from_a_default() -> None:
    for name in ("step", "sender", "hint", "smell_grid", "commit", "timestamp"):
        with pytest.raises(ValidationError):
            KitTurnMessage.model_validate({k: v for k, v in TURN.items() if k != name})


def test_a_strict_envelope_is_not_silently_accepted_as_a_kit_turn() -> None:
    """No fallback: a `{kind, payload}` body carries none of the required keys."""
    with pytest.raises(ValidationError):
        KitTurnMessage.model_validate({"kind": "commitment", "payload": {"h_commit": "a" * 64}})


def test_the_turn_carries_the_sub_game_from_context_never_from_the_wire() -> None:
    """A kit turn numbers only its own chain; the sub-game is the handshake's."""
    value = decode_kit_turn(KitTurnMessage.model_validate(TURN))
    commitment = value.commitment(3)

    assert commitment.cursor.sub_game == 3
    assert commitment.cursor.step == 7
    assert commitment.h_commit == Sha256Digest("a" * 64)


@pytest.mark.parametrize("claim", RESULT_CLAIMS)
def test_every_outcome_the_pinned_peer_can_claim_is_accepted(claim: str) -> None:
    value = decode_kit_audit(KitAuditPayload.model_validate(AUDIT | {"result_claim": claim}))

    assert value.result_claim is KitResultClaim(claim)


def test_the_audit_records_arrive_whole_so_their_digests_can_be_recomputed() -> None:
    value = decode_kit_audit(KitAuditPayload.model_validate(AUDIT))

    assert value.sender is KitRole.POLICE
    assert len(value.records) == 1
    assert value.records[0].payload.value == {"step": 1, "move": "MOVE:N"}
    assert value.records[0].nonce == "0" * 32
    assert value.records[0].commit == Sha256Digest("a" * 64)


def test_an_audit_missing_a_required_key_is_refused() -> None:
    for name in ("sender", "records", "result_claim"):
        with pytest.raises(ValidationError):
            KitAuditPayload.model_validate({k: v for k, v in AUDIT.items() if k != name})


@pytest.mark.parametrize("kind", CONTROL_KINDS)
def test_every_pinned_control_kind_decodes(kind: str) -> None:
    value = decode_kit_control(KitControlMessage.model_validate(CONTROL | {"kind": kind}))

    assert value.kind is KitControlKind(kind)
    assert value.sender is KitRole.POLICE


def test_a_control_command_outside_the_pinned_vocabulary_is_refused() -> None:
    with pytest.raises(ValidationError):
        KitControlMessage.model_validate(CONTROL | {"kind": "restart_everything"})


def test_a_greeting_decodes_its_required_and_declared_optional_members() -> None:
    value = decode_kit_greeting(KitNegotiateMessage.model_validate(NEGOTIATION))

    assert value.group_id == "team-aleph"
    assert value.terms.value == {"grid_size": 10, "max_steps": 35}
    assert value.nonce == "a1a2a3a4b1b2b3b4c1c2c3c4d1d2d3d4"
    assert value.role is KitRole.POLICE
    assert value.sub_game_number == 1
    assert value.game_uid == "1e73c318-5b29-4a7b-1c60-ecb8286265f0"


def test_an_omitted_optional_member_is_silence_and_never_a_default() -> None:
    """Omission never refuses, in either direction (pinned SPEC sections 7-7.3)."""
    bare = {k: NEGOTIATION[k] for k in ("terms", "nonce", "signature", "group_id")}
    value = decode_kit_greeting(KitNegotiateMessage.model_validate(bare))

    assert value.role is None
    assert value.sub_game_number is None
    assert value.game_uid is None
    assert value.identity is None


def test_a_greeting_missing_a_required_key_is_refused() -> None:
    for name in ("terms", "nonce", "signature", "group_id"):
        with pytest.raises(ValidationError):
            KitNegotiateMessage.model_validate(
                {k: v for k, v in NEGOTIATION.items() if k != name},
            )
