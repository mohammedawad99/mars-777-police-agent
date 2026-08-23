"""Every transported family survives DTO encode/decode with semantic equality.

Semantic equality is necessary but not sufficient, so the hash-relevant families
are additionally checked at the **bytes** level: a codec that rebuilt an equal
value with different canonical bytes would still make two peers refuse each
other.
"""

import pytest
from peer_ops import (
    acknowledgement,
    agreement,
    commitment,
    final_nonce,
    lock_evidence,
    proposal,
    reveal,
    step0_exchange,
)
from r16_builders import GROUP_A, GROUP_B

from mars777_police.app.participant_slots import slot_of
from mars777_police.protocol.canonical import canonical_json_bytes
from mars777_police.protocol.config_lock import config_sha256, lock_context_core
from mars777_police.protocol.config_projection import config_core
from mars777_police.protocol.declaration import step0_core
from mars777_police.protocol.keyed_auth import CONFIG_CONTEXT, STEP0_CONTEXT, auth_input
from mars777_police.transport.codec_declaration import decode_step0, encode_step0
from mars777_police.transport.codec_final import (
    decode_final_nonce,
    decode_result_agreement,
    encode_final_nonce,
    encode_result_agreement,
)
from mars777_police.transport.codec_pregame import (
    decode_lock,
    decode_proposal,
    encode_lock,
    encode_proposal,
)
from mars777_police.transport.codec_turn import (
    decode_acknowledgement,
    decode_commitment,
    decode_reveal,
    encode_acknowledgement,
    encode_commitment,
    encode_reveal,
)


@pytest.mark.parametrize("vram", [None, 24], ids=["cpu-only", "gpu"])
def test_step0_round_trips_on_both_hardware_branches(vram: int | None) -> None:
    original = step0_exchange(vram)
    assert decode_step0(encode_step0(original)) == original


@pytest.mark.parametrize("vram", [None, 24], ids=["cpu-only", "gpu"])
def test_step0_authenticated_bytes_are_identical_after_transport(vram: int | None) -> None:
    original = step0_exchange(vram)
    rebuilt = decode_step0(encode_step0(original))
    before = auth_input(STEP0_CONTEXT, step0_core(original.declaration, GROUP_B))
    after = auth_input(STEP0_CONTEXT, step0_core(rebuilt.declaration, GROUP_B))
    assert before == after


def test_a_cpu_only_core_still_omits_vram_after_transport() -> None:
    rebuilt = decode_step0(encode_step0(step0_exchange(None)))
    raw = canonical_json_bytes(step0_core(rebuilt.declaration, GROUP_B))
    assert b'"vram_gb"' not in raw
    assert b"null" not in raw
    assert b'"gpu":false' in raw
    seated = getattr(rebuilt.declaration.teams, slot_of(GROUP_A, GROUP_B, GROUP_B))
    assert seated is not None
    assert seated.hardware.vram_gb is None


def test_config_proposal_round_trips_with_identical_canonical_bytes() -> None:
    original = proposal()
    rebuilt = decode_proposal(encode_proposal(original))
    assert rebuilt == original
    assert canonical_json_bytes(config_core(rebuilt.config)) == canonical_json_bytes(
        config_core(original.config)
    )
    assert config_sha256(rebuilt.config) == config_sha256(original.config)


def test_config_lock_round_trips_with_identical_auth_bytes() -> None:
    original = lock_evidence()
    rebuilt = decode_lock(encode_lock(original))
    assert rebuilt == original
    before = auth_input(CONFIG_CONTEXT, lock_context_core(original.context))
    assert auth_input(CONFIG_CONTEXT, lock_context_core(rebuilt.context)) == before


def test_commitment_round_trips_and_preserves_the_digest() -> None:
    original = commitment()
    rebuilt = decode_commitment(encode_commitment(original))
    assert rebuilt == original
    assert rebuilt.h_commit.value == original.h_commit.value


def test_acknowledgement_round_trips_and_gains_no_accepted_member() -> None:
    original = acknowledgement()
    rebuilt = decode_acknowledgement(encode_acknowledgement(original))
    assert rebuilt == original
    assert not hasattr(rebuilt, "accepted")


def test_reveal_round_trips_and_never_carries_a_nonce() -> None:
    original = reveal()
    rebuilt = decode_reveal(encode_reveal(original))
    assert rebuilt == original
    wire = encode_reveal(original).model_dump(mode="json")
    assert "nonce" not in str(wire)
    assert set(wire) == {"cursor", "action", "hint", "capture_claim", "scent_emission"}
    assert wire["capture_claim"] is None


def test_a_barrier_reveal_round_trips_through_the_tagged_action() -> None:
    from peer_ops import CURSOR

    from mars777_police.app.peer_turn_messages import Reveal
    from mars777_police.domain.actions import BarrierAction
    from mars777_police.domain.board import Position

    original = Reveal(CURSOR, BarrierAction(Position(5, 6)), "blocked")
    rebuilt = decode_reveal(encode_reveal(original))
    assert rebuilt == original
    assert encode_reveal(original).action.value == [5, 6]


def test_final_nonce_reveal_round_trips() -> None:
    original = final_nonce()
    assert decode_final_nonce(encode_final_nonce(original)) == original


def test_result_agreement_round_trips_and_carries_no_digest() -> None:
    original = agreement()
    rebuilt = decode_result_agreement(encode_result_agreement(original))
    assert rebuilt == original
    wire = encode_result_agreement(original).model_dump(mode="json")
    assert "result_sha256" not in wire
    assert "mutual_agreement" not in wire
