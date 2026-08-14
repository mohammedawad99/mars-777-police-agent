"""The ten closed profile types and the eleven-member InteropProfileSet."""

import dataclasses

import pytest
from pregame_builders import profiles

from mars777_police.app.auth_values import AuthProfile, KeyId
from mars777_police.app.interop_profiles import (
    CanonicalizationProfile,
    CommitmentCodec,
    CompatibilityProfile,
    InteropProfileSet,
    InvalidInteropProfileSetError,
    NonceRepresentationProfile,
    ResultProfile,
    SealedRecordProfile,
    SeriesConvention,
    StateRepresentationProfile,
    ToolNameProfile,
)

CLOSED_TYPES = (
    SeriesConvention,
    AuthProfile,
    CommitmentCodec,
    ResultProfile,
    CompatibilityProfile,
    ToolNameProfile,
    CanonicalizationProfile,
    SealedRecordProfile,
    StateRepresentationProfile,
    NonceRepresentationProfile,
)
SINGLE_MEMBER_TYPES = (
    CanonicalizationProfile,
    SealedRecordProfile,
    StateRepresentationProfile,
    NonceRepresentationProfile,
)


def test_there_are_ten_closed_profile_types() -> None:
    assert len(CLOSED_TYPES) == 10


def test_there_are_nineteen_enum_member_memberships() -> None:
    """Eighteen, plus the fifth compatibility posture V2 added."""
    assert sum(len(profile_type) for profile_type in CLOSED_TYPES) == 19


def test_there_are_eighteen_unique_serialized_tokens() -> None:
    tokens = {member.value for profile_type in CLOSED_TYPES for member in profile_type}
    assert len(tokens) == 18
    assert "STRICT_COUNTED_MATCH_TURN_OUTCOME_V1" in tokens, "the legacy token survives"
    assert "STRICT_COUNTED_MATCH_TURN_OUTCOME_SCENT_V2" in tokens


def test_the_duplicate_token_is_attachment_compatibility() -> None:
    assert ResultProfile.LECTURER_ATTACHMENT_COMPATIBILITY.value == (
        CompatibilityProfile.LECTURER_ATTACHMENT_COMPATIBILITY.value
    )
    assert (
        ResultProfile.LECTURER_ATTACHMENT_COMPATIBILITY
        is not CompatibilityProfile.LECTURER_ATTACHMENT_COMPATIBILITY
    )
    assert type(ResultProfile.LECTURER_ATTACHMENT_COMPATIBILITY) is not CompatibilityProfile


def test_four_types_have_exactly_one_current_v1_member() -> None:
    assert all(len(profile_type) == 1 for profile_type in SINGLE_MEMBER_TYPES)
    assert len(SINGLE_MEMBER_TYPES) == 4


def test_every_serialized_value_equals_its_identifier() -> None:
    for profile_type in CLOSED_TYPES:
        for member in profile_type:
            assert member.value == member.name


@pytest.mark.parametrize(
    ("profile_type", "expected"),
    [
        (SeriesConvention, ["FIXED_ROLE", "REFERENCE_ODD_EVEN_ALTERNATION"]),
        (CommitmentCodec, ["STRICT_PROJECT_COMMITMENT", "LECTURER_REFERENCE_COMMITMENT"]),
        (ResultProfile, ["STRICT_PROJECT_RESULT", "LECTURER_ATTACHMENT_COMPATIBILITY"]),
        (
            CompatibilityProfile,
            [
                "STRICT_COUNTED_MATCH",
                "STRICT_COUNTED_MATCH_TURN_OUTCOME_V1",
                "STRICT_COUNTED_MATCH_TURN_OUTCOME_SCENT_V2",
                "LECTURER_REFERENCE_COMPATIBILITY",
                "LECTURER_ATTACHMENT_COMPATIBILITY",
            ],
        ),
        (ToolNameProfile, ["PROJECT_LOGICAL_OPERATIONS", "LECTURER_REFERENCE_ALIASES"]),
        (CanonicalizationProfile, ["CANONICAL_JSON_V1"]),
        (SealedRecordProfile, ["SEALED_RECORD_V1"]),
        (StateRepresentationProfile, ["SEALED_STATE_V1"]),
        (NonceRepresentationProfile, ["LOWER_HEX_32"]),
    ],
)
def test_exact_vocabularies(profile_type: type, expected: list[str]) -> None:
    assert [member.value for member in profile_type] == expected  # type: ignore[misc]


def test_valid_profile_set_round_trips() -> None:
    value = profiles()
    assert value.key_id == KeyId("match-key_1.0")
    assert value.auth_profile is AuthProfile.HMAC_SHA256


def test_profile_set_is_immutable_and_has_eleven_members() -> None:
    assert len(dataclasses.fields(InteropProfileSet)) == 11
    with pytest.raises(dataclasses.FrozenInstanceError):
        profiles().key_id = KeyId("other")  # type: ignore[misc]


@pytest.mark.parametrize(
    ("field", "bad"),
    [
        ("series_convention", "FIXED_ROLE"),
        ("auth_profile", "HMAC_SHA256"),
        ("key_id", "match-key_1.0"),
        ("commitment_codec", "STRICT_PROJECT_COMMITMENT"),
        ("result_profile", "STRICT_PROJECT_RESULT"),
        ("compatibility_profile", "STRICT_COUNTED_MATCH_TURN_OUTCOME_SCENT_V2"),
        ("tool_name_profile", "PROJECT_LOGICAL_OPERATIONS"),
        ("canonicalization_profile", "CANONICAL_JSON_V1"),
        ("sealed_record_profile", "SEALED_RECORD_V1"),
        ("state_representation_profile", "SEALED_STATE_V1"),
        ("nonce_representation_profile", "LOWER_HEX_32"),
    ],
)
def test_raw_strings_are_never_promoted_to_members(field: str, bad: str) -> None:
    with pytest.raises(InvalidInteropProfileSetError, match=f"{field} must be a"):
        profiles(**{field: bad})
