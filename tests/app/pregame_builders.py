"""Shared builders for the pregame semantic-value tests."""

from decimal import Decimal

from mars777_police.app.artifact_values import GitCommitSha, UtcTimestamp
from mars777_police.app.auth_values import AuthProfile, AuthProof, KeyId
from mars777_police.app.declaration_values import Declaration, DeclarationTeams, DeclarationTimes
from mars777_police.app.interop_profiles import (
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
from mars777_police.app.team_declaration_values import (
    HardwareDeclaration,
    RepositoryLinks,
    TeamDeclaration,
)

COMMIT = "2113e68d141ab087b849f83a7d91d66620e8ad85"
START = "2026-08-07T00:00:00Z"
END = "2026-08-07T01:00:00Z"
KEY = KeyId("match-key_1.0")


def hardware(**over: object) -> HardwareDeclaration:
    fields: dict[str, object] = {
        "os": "Linux",
        "cpu_cores": 8,
        "cpu_freq_ghz": Decimal("3.2"),
        "ram_gb": 16,
        "gpu": False,
        "vram_gb": None,
    }
    fields.update(over)
    return HardwareDeclaration(**fields)  # type: ignore[arg-type]


def team(**over: object) -> TeamDeclaration:
    fields: dict[str, object] = {
        "group_id": "MaRs-777",
        "group_name": "MaRs-777",
        "members": ("id-1001",),
        "repos": RepositoryLinks("https://example.invalid/p", "https://example.invalid/t"),
        "mcp_endpoint": "https://example.invalid/mcp",
        "hardware": hardware(),
        "llm_model": "template",
        "code_version": "0.0.0",
        "github_commit": GitCommitSha(COMMIT),
    }
    fields.update(over)
    return TeamDeclaration(**fields)  # type: ignore[arg-type]


def times(end: str | None = None) -> DeclarationTimes:
    return DeclarationTimes(UtcTimestamp(START), UtcTimestamp(end) if end else None)


def declaration(**over: object) -> Declaration:
    fields: dict[str, object] = {
        "game_id": "mars777-g1",
        "game_uid": "uid0001",
        "token_budget_per_series": 200000,
        "times": times(),
        "teams": DeclarationTeams(team(), None),
    }
    fields.update(over)
    return Declaration(**fields)  # type: ignore[arg-type]


def profiles(**over: object) -> InteropProfileSet:
    fields: dict[str, object] = {
        "series_convention": SeriesConvention.FIXED_ROLE,
        "auth_profile": AuthProfile.HMAC_SHA256,
        "key_id": KEY,
        "commitment_codec": CommitmentCodec.STRICT_PROJECT_COMMITMENT,
        "result_profile": ResultProfile.STRICT_PROJECT_RESULT,
        "compatibility_profile": CompatibilityProfile.STRICT_COUNTED_MATCH,
        "tool_name_profile": ToolNameProfile.PROJECT_LOGICAL_OPERATIONS,
        "canonicalization_profile": CanonicalizationProfile.CANONICAL_JSON_V1,
        "sealed_record_profile": SealedRecordProfile.SEALED_RECORD_V1,
        "state_representation_profile": StateRepresentationProfile.SEALED_STATE_V1,
        "nonce_representation_profile": NonceRepresentationProfile.LOWER_HEX_32,
    }
    fields.update(over)
    return InteropProfileSet(**fields)  # type: ignore[arg-type]


def proof(profile: AuthProfile = AuthProfile.HMAC_SHA256, key: KeyId = KEY) -> AuthProof:
    width = 64 if profile is AuthProfile.HMAC_SHA256 else 128
    return AuthProof(profile, key, "a" * width)
