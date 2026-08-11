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


def encode_profiles(profiles: InteropProfileSet) -> InteropProfileSetWire:
    """Render the profile set; every token is its identifier, byte for byte."""
    return InteropProfileSetWire(
        series_convention=profiles.series_convention.value,
        auth_profile=profiles.auth_profile.value,
        key_id=profiles.key_id.value,
        commitment_codec=profiles.commitment_codec.value,
        result_profile=profiles.result_profile.value,
        compatibility_profile=profiles.compatibility_profile.value,
        tool_name_profile=profiles.tool_name_profile.value,
        canonicalization_profile=profiles.canonicalization_profile.value,
        sealed_record_profile=profiles.sealed_record_profile.value,
        state_representation_profile=profiles.state_representation_profile.value,
        nonce_representation_profile=profiles.nonce_representation_profile.value,
    )
