"""Codec for the keyed-auth envelope and the eleven series-wide profiles.

Split from `codec_config` by ownership: the profile set and the `AuthProof` are
series-wide values that the lock context binds, while the 35-member core is the
per-sub-game physics contract.

Only `key_id` ever crosses. Key material has no wire representation at all, here
or anywhere else.
"""

from ..app.auth_values import AuthProfile, AuthProof, KeyId
from ..app.interop_profiles import (
    CanonicalizationProfile,
    CommitmentCodec,
    CompatibilityProfile,
    InteropProfileSet,
    NonceRepresentationProfile,
    ResultProfile,
    SealedRecordProfile,
    SeriesConvention,
    StateRepresentationProfile,
    ToolNameProfile,
)
from .wire_config import AuthProofWire, InteropProfileSetWire


def decode_auth(wire: AuthProofWire) -> AuthProof:
    """Rebuild an `AuthProof`; the semantic type re-checks the proof width."""
    return AuthProof(AuthProfile(wire.profile), KeyId(wire.key_id), wire.value)


def encode_auth(proof: AuthProof) -> AuthProofWire:
    """Render an `AuthProof`. Only `key_id` travels - never key material."""
    return AuthProofWire(profile=proof.profile.value, key_id=proof.key_id.value, value=proof.value)


def decode_profiles(wire: InteropProfileSetWire) -> InteropProfileSet:
    """Rebuild the eleven series-wide profile values from their exact tokens."""
    return InteropProfileSet(
        SeriesConvention(wire.series_convention),
        AuthProfile(wire.auth_profile),
        KeyId(wire.key_id),
        CommitmentCodec(wire.commitment_codec),
        ResultProfile(wire.result_profile),
        CompatibilityProfile(wire.compatibility_profile),
        ToolNameProfile(wire.tool_name_profile),
        CanonicalizationProfile(wire.canonicalization_profile),
        SealedRecordProfile(wire.sealed_record_profile),
        StateRepresentationProfile(wire.state_representation_profile),
        NonceRepresentationProfile(wire.nonce_representation_profile),
    )


_WIRE_CODECS = (
    CommitmentCodec.STRICT_PROJECT_COMMITMENT,
    CommitmentCodec.LECTURER_REFERENCE_COMMITMENT,
)
_WIRE_RESULTS = (
    ResultProfile.STRICT_PROJECT_RESULT,
    ResultProfile.LECTURER_ATTACHMENT_COMPATIBILITY,
)
"""What the frozen `InteropProfileSetWire` literals can carry today.

The KIT members are deliberately absent from both. Widening a wire literal is a
schema change, and this stage owns the local authorities rather than the
transport, so the encoder refuses rather than emitting a token the receiver's
schema would reject. Transmitting them is Stage 8A-1T's work.
"""


def encode_profiles(profiles: InteropProfileSet) -> InteropProfileSetWire:
    """Render the profile set; every token is its identifier, byte for byte."""
    codec, result = profiles.commitment_codec, profiles.result_profile
    for value, carried in ((codec, _WIRE_CODECS), (result, _WIRE_RESULTS)):
        if value not in carried:
            raise ValueError(
                f"{value.value} has no representation in the frozen profile wire;"
                " transmitting it is Stage 8A-1T's transport work, not this codec's"
            )
    return InteropProfileSetWire(
        series_convention=profiles.series_convention.value,
        auth_profile=profiles.auth_profile.value,
        key_id=profiles.key_id.value,
        commitment_codec=codec.value,  # type: ignore[arg-type]
        result_profile=result.value,  # type: ignore[arg-type]
        compatibility_profile=profiles.compatibility_profile.value,
        tool_name_profile=profiles.tool_name_profile.value,
        canonicalization_profile=profiles.canonicalization_profile.value,
        sealed_record_profile=profiles.sealed_record_profile.value,
        state_representation_profile=profiles.state_representation_profile.value,
        nonce_representation_profile=profiles.nonce_representation_profile.value,
    )
