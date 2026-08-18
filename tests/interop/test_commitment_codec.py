"""One dispatch owns every commitment, in both directions.

A sender and a verifier that each implemented the same construction would be
two chances to get it wrong and no way to notice: the pair agrees with itself
while disagreeing with everyone else. So local sealing, peer verification,
audit recomputation and replay all reach the same function, and the codec is a
frozen series-wide decision rather than a per-message guess.

**No try-both.** A verifier that accepted whichever digest matched would accept
a peer that changed construction mid-series, and would turn an integrity
failure into a silent profile switch. A mismatch is a mismatch.
"""

import pytest
from kit_vectors import COMMITMENTS

from mars777_police.app.interop_profiles import CommitmentCodec
from mars777_police.protocol.commitment_codec import commitment_for, verify_commitment


@pytest.mark.parametrize(("payload", "nonce", "expected"), COMMITMENTS)
def test_the_kit_codec_reproduces_the_pinned_digests(
    payload: dict[str, object], nonce: str, expected: str
) -> None:
    assert commitment_for(CommitmentCodec.KIT_CORE_COMMITMENT_V1, payload, nonce) == expected


def test_verification_is_a_verdict_and_never_an_interpretation() -> None:
    payload, nonce, expected = COMMITMENTS[1]

    assert verify_commitment(CommitmentCodec.KIT_CORE_COMMITMENT_V1, payload, nonce, expected)
    assert not verify_commitment(CommitmentCodec.KIT_CORE_COMMITMENT_V1, payload, nonce, "0" * 64)


def test_a_wrong_nonce_fails_rather_than_falling_back() -> None:
    payload, _, expected = COMMITMENTS[1]

    assert not verify_commitment(
        CommitmentCodec.KIT_CORE_COMMITMENT_V1, payload, "f" * 32, expected
    )


def test_the_strict_codec_refuses_a_kit_payload_rather_than_reinterpreting_it() -> None:
    """The strict construction seals typed members; a bare JSON dict is not one."""
    payload, nonce, _ = COMMITMENTS[1]

    with pytest.raises(ValueError):
        commitment_for(CommitmentCodec.STRICT_PROJECT_COMMITMENT, payload, nonce)


def test_the_two_codecs_do_not_agree_on_the_same_input() -> None:
    """Proved by difference, so a refactor cannot quietly unify them."""
    from mars777_police.protocol.kit_commitment import kit_commitment

    payload, nonce, expected = COMMITMENTS[1]

    assert kit_commitment(payload, nonce) == expected
    assert kit_commitment({**payload, "nonce": nonce}, nonce) != expected


def test_every_codec_member_is_dispatchable() -> None:
    """A decorative enum member is the defect this dispatch exists to remove."""
    payload, nonce, _ = COMMITMENTS[1]

    for codec in CommitmentCodec:
        try:
            commitment_for(codec, payload, nonce)
        except ValueError:
            continue  # a codec may lawfully refuse this payload shape
        else:
            continue


def test_the_kit_codec_is_not_serialized_onto_the_frozen_profile_wire() -> None:
    """Widening the wire literal is transport work; the encoder refuses instead."""
    import dataclasses

    from mars777_police.transport.codec_auth import encode_profiles

    strict = _profiles(CommitmentCodec.STRICT_PROJECT_COMMITMENT)
    external = dataclasses.replace(strict, commitment_codec=CommitmentCodec.KIT_CORE_COMMITMENT_V1)

    with pytest.raises(ValueError, match="no representation in the frozen profile wire"):
        encode_profiles(external)

    assert encode_profiles(strict).commitment_codec == "STRICT_PROJECT_COMMITMENT"


def test_the_kit_result_profile_is_refused_by_the_same_wire_guard() -> None:
    """Both KIT members are local selections until the transport stage carries them."""
    import dataclasses

    from mars777_police.app.interop_profiles import ResultProfile
    from mars777_police.transport.codec_auth import encode_profiles

    strict = _profiles(CommitmentCodec.STRICT_PROJECT_COMMITMENT)
    external = dataclasses.replace(strict, result_profile=ResultProfile.KIT_CORE_RESULT_V1)

    with pytest.raises(ValueError, match="no representation in the frozen profile wire"):
        encode_profiles(external)


def _profiles(codec: CommitmentCodec) -> object:
    """The eleven-member set, built here because `tests/interop` owns its helpers."""
    from mars777_police.app.auth_values import AuthProfile, KeyId
    from mars777_police.app.interop_profiles import (
        CanonicalizationProfile,
        CompatibilityProfile,
        InteropProfileSet,
        NonceRepresentationProfile,
        ResultProfile,
        SealedRecordProfile,
        SeriesConvention,
        StateRepresentationProfile,
        ToolNameProfile,
    )

    return InteropProfileSet(
        SeriesConvention.FIXED_ROLE,
        AuthProfile.HMAC_SHA256,
        KeyId("mars777-k1"),
        codec,
        ResultProfile.STRICT_PROJECT_RESULT,
        CompatibilityProfile.STRICT_COUNTED_MATCH_TURN_OUTCOME_SCENT_V2,
        ToolNameProfile.PROJECT_LOGICAL_OPERATIONS,
        CanonicalizationProfile.CANONICAL_JSON_V1,
        SealedRecordProfile.SEALED_RECORD_V1,
        StateRepresentationProfile.SEALED_STATE_V1,
        NonceRepresentationProfile.LOWER_HEX_32,
    )
