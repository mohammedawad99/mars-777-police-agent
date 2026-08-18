"""Which commitment construction a series froze, as its own small authority.

Split out of `interop_profiles` when the KIT member arrived: that module is the
eleven-member profile *set*, and a codec that now dispatches real behaviour has
outgrown being one line inside it. The set still names it; this module owns
what the names mean.
"""

from enum import StrEnum


class CommitmentCodec(StrEnum):
    """Which commitment construction both peers agreed to use."""

    STRICT_PROJECT_COMMITMENT = "STRICT_PROJECT_COMMITMENT"
    """Our eight-member sealed record, canonicalised whole - nonce inside."""

    LECTURER_REFERENCE_COMMITMENT = "LECTURER_REFERENCE_COMMITMENT"
    """The reference listing's form, represented for compatibility mapping."""

    KIT_CORE_COMMITMENT_V1 = "KIT_CORE_COMMITMENT_V1"
    """The pinned kit's form: `SHA256(kit_canonical(payload)|nonce)`, nonce outside."""
