"""The eleven SERIES-WIDE interoperability choices frozen at ``CONFIG_LOCKED``.

Ten closed profile types plus one ``KeyId``. Every serialized value **is** its
identifier: no alias, no case folding, no normalisation, and no raw string is
ever silently promoted to a member - the caller constructs the typed value.

Four types have exactly one current-v1 member (`CONFIG_CONTRACT.md` R14-R1-D).
That is deliberate: both peers echo the one required profile and a differing echo
refuses counted play before ``CONFIG_LOCKED``. Single-member enums are kept so
the lock binds an explicit token rather than an implicit assumption.

``LECTURER_ATTACHMENT_COMPATIBILITY`` is intentionally the serialized value of a
member of **two** distinct types; they are never interchangeable, and neither is
renamed to make token strings globally unique.
"""

from dataclasses import dataclass
from enum import StrEnum

from .auth_values import AuthProfile, KeyId


class InvalidInteropProfileSetError(ValueError):
    """Raised when the series-wide profile set is structurally malformed."""


class SeriesConvention(StrEnum):
    """How roles are assigned across the sub-games of a series.

    **Neither member is source-mandated** (`PRD05-FR-031`): alternation is a
    reference/attachment convention and a fixed role is equally a project choice.
    """

    FIXED_ROLE = "FIXED_ROLE"
    REFERENCE_ODD_EVEN_ALTERNATION = "REFERENCE_ODD_EVEN_ALTERNATION"


class CommitmentCodec(StrEnum):
    """Which commitment construction both peers agreed to use."""

    STRICT_PROJECT_COMMITMENT = "STRICT_PROJECT_COMMITMENT"
    LECTURER_REFERENCE_COMMITMENT = "LECTURER_REFERENCE_COMMITMENT"


class ResultProfile(StrEnum):
    """Which result-artifact shape is emitted."""

    STRICT_PROJECT_RESULT = "STRICT_PROJECT_RESULT"
    LECTURER_ATTACHMENT_COMPATIBILITY = "LECTURER_ATTACHMENT_COMPATIBILITY"


COUNTED_TURN_PROFILE = "STRICT_COUNTED_MATCH_TURN_OUTCOME_V1"
"""The only posture whose turn contract this build speaks."""


class CompatibilityProfile(StrEnum):
    """The compatibility posture, and the turn contract it implies.

    R8 made a Reveal answer with `TurnOutcome` rather than a legality `bool`, so
    the posture names it and `turn_contract_gate` refuses a mismatch pre-lock.
    """

    STRICT_COUNTED_MATCH = "STRICT_COUNTED_MATCH"
    """**Legacy**: the pre-R8 legality-bool result; never a counted emitter now."""

    STRICT_COUNTED_MATCH_TURN_OUTCOME_V1 = "STRICT_COUNTED_MATCH_TURN_OUTCOME_V1"
    """Current counted contract: `Reveal(+capture_claim)` -> `TurnOutcome`."""
    LECTURER_REFERENCE_COMPATIBILITY = "LECTURER_REFERENCE_COMPATIBILITY"
    LECTURER_ATTACHMENT_COMPATIBILITY = "LECTURER_ATTACHMENT_COMPATIBILITY"


class ToolNameProfile(StrEnum):
    """Whether the reference tool aliases are enabled alongside our operations.

    It never changes internal operation identity - only which names an ingress
    additionally answers to (`PRD02-FR-034`, not book-mandated).
    """

    PROJECT_LOGICAL_OPERATIONS = "PROJECT_LOGICAL_OPERATIONS"
    LECTURER_REFERENCE_ALIASES = "LECTURER_REFERENCE_ALIASES"


class CanonicalizationProfile(StrEnum):
    """Names the complete frozen NDEC-003 v1 canonicalization bundle."""

    CANONICAL_JSON_V1 = "CANONICAL_JSON_V1"


class SealedRecordProfile(StrEnum):
    """Names the NDEC-001 v1 sealed-record and action-encoding bundle.

    Distinct from ``CommitmentCodec``: that selects strict-versus-reference
    commitment behaviour, this identifies the sealed-record semantics itself.
    """

    SEALED_RECORD_V1 = "SEALED_RECORD_V1"


class StateRepresentationProfile(StrEnum):
    """Names the NDEC-002 / JDEC-012 sealed ``state`` representation."""

    SEALED_STATE_V1 = "SEALED_STATE_V1"


class NonceRepresentationProfile(StrEnum):
    """Names the current-v1 nonce representation ``[0-9a-f]{32}``."""

    LOWER_HEX_32 = "LOWER_HEX_32"


@dataclass(frozen=True, slots=True)
class InteropProfileSet:
    """Every series-wide choice the config lock context binds.

    All eleven members are required and explicitly typed. There is **no default
    anywhere**: a silent default is exactly how two peers end up believing they
    agreed on different things.
    """

    series_convention: SeriesConvention
    auth_profile: AuthProfile
    key_id: KeyId
    commitment_codec: CommitmentCodec
    result_profile: ResultProfile
    compatibility_profile: CompatibilityProfile
    tool_name_profile: ToolNameProfile
    canonicalization_profile: CanonicalizationProfile
    sealed_record_profile: SealedRecordProfile
    state_representation_profile: StateRepresentationProfile
    nonce_representation_profile: NonceRepresentationProfile

    def __post_init__(self) -> None:
        for name, expected in (
            ("series_convention", SeriesConvention),
            ("auth_profile", AuthProfile),
            ("key_id", KeyId),
            ("commitment_codec", CommitmentCodec),
            ("result_profile", ResultProfile),
            ("compatibility_profile", CompatibilityProfile),
            ("tool_name_profile", ToolNameProfile),
            ("canonicalization_profile", CanonicalizationProfile),
            ("sealed_record_profile", SealedRecordProfile),
            ("state_representation_profile", StateRepresentationProfile),
            ("nonce_representation_profile", NonceRepresentationProfile),
        ):
            value = getattr(self, name)
            if type(value) is not expected:
                raise InvalidInteropProfileSetError(
                    f"{name} must be a {expected.__name__}, got {type(value).__name__}",
                )
