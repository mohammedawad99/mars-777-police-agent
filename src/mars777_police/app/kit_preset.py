"""One explicit choice, made before play, that selects a whole external profile.

The alternative is eight independent switches an operator has to get right
together - and any single one left on the internal default produces a peer that
agrees on every game value and disagrees on the bytes, which is the failure
mode hardest to diagnose from the far side of a tunnel. So external mode is a
single selection resolving to a frozen `InteropProfileSet`.

**Chosen before the series, never inferred.** A profile cannot be negotiated by
the very messages whose encoding it governs, and probing - try one construction,
fall back to the other - would turn an integrity failure into a silent
downgrade. The operator selects the mode out of band.

**`KIT_CORE_V1` is a local name.** The pinned kit defines no such token, so it
is never serialized: what a future transport would carry is the profile's own
eleven members, each of which the kit or this project already names.

Interoperability buys no discount on authentication. Both modes keep
`HMAC_SHA256` and the same nonce representation, because the kit's terms digest
is an unkeyed content agreement and was never a substitute for knowing who is
speaking. And both offer `FIXED_ROLE` only - alternation is not implemented
anywhere in this build, so offering it would be promising what we cannot do.
"""

from enum import StrEnum

from .auth_values import AuthProfile, KeyId
from .commitment_codecs import CommitmentCodec
from .interop_profiles import (
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


class ExternalMode(StrEnum):
    """Which profile family a series was launched to speak."""

    STRICT_INTERNAL = "STRICT_INTERNAL"
    """Our own construction: the eight-member sealed record, compact result bytes."""

    KIT_CORE_V1 = "KIT_CORE_V1"
    """The pinned kit's constructions. A local selection name, never sent."""


def external_profiles(mode: ExternalMode, key_id: KeyId) -> InteropProfileSet:
    """The frozen profile set *mode* selects, for the whole series."""
    kit = mode is ExternalMode.KIT_CORE_V1
    return InteropProfileSet(
        SeriesConvention.FIXED_ROLE,
        AuthProfile.HMAC_SHA256,
        key_id,
        CommitmentCodec.KIT_CORE_COMMITMENT_V1
        if kit
        else CommitmentCodec.STRICT_PROJECT_COMMITMENT,
        ResultProfile.KIT_CORE_RESULT_V1 if kit else ResultProfile.STRICT_PROJECT_RESULT,
        CompatibilityProfile.STRICT_COUNTED_MATCH_TURN_OUTCOME_SCENT_V2,
        ToolNameProfile.PROJECT_LOGICAL_OPERATIONS,
        CanonicalizationProfile.CANONICAL_JSON_V1,
        SealedRecordProfile.SEALED_RECORD_V1,
        StateRepresentationProfile.SEALED_STATE_V1,
        NonceRepresentationProfile.LOWER_HEX_32,
    )
