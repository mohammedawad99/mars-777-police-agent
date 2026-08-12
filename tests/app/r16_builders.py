"""Shared R16 fixtures: two participants, one config, one finished series.

Duplicated per test directory on purpose - `tests/app` and `tests/protocol` have
no package, so each owns the helpers it imports. `GROUP-XY` is byte-wise **lower**
than `MaRs-777` while sitting in the `group_b` slot, so every proposer test
exercises the case where the slot and the deterministic rule disagree.
"""

from decimal import Decimal

from mars777_police.app.artifact_values import GitCommitSha, UtcTimestamp
from mars777_police.app.auth_values import AuthProfile, KeyId
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
from mars777_police.app.result_core_runtime import SubGameOutcomeLine
from mars777_police.app.result_core_values import CumulativeResult
from mars777_police.app.result_identity_values import GithubLinks, ResultParticipants
from mars777_police.app.result_values import ResultContribution, ResultContributionEntry
from mars777_police.app.team_declaration_values import (
    HardwareDeclaration,
    RepositoryLinks,
    TeamDeclaration,
)
from mars777_police.domain.board import Position
from mars777_police.domain.config_league_sections import (
    NetworkAndLeagueTerms,
    PheromoneTerms,
    RateLimiterTerms,
)
from mars777_police.domain.config_sections import (
    BoardAndAgentsTerms,
    MovementAndBarrierTerms,
    ScoringTerms,
    WorldTerms,
)
from mars777_police.domain.negotiated_config import NegotiatedConfig
from mars777_police.domain.terminal import Outcome

GROUP_A = "MaRs-777"
GROUP_B = "GROUP-XY"
COMMIT_A = GitCommitSha("a" * 40)
COMMIT_B = GitCommitSha("b" * 40)
GAME_ID = "mars777-vs-groupx-2026w1-uid0001"
GAME_UID = "uid0001"
START = UtcTimestamp("2026-08-07T00:00:00Z")
STAMP = UtcTimestamp("2026-08-07T01:00:00Z")
KEY_ID = KeyId("mars777-k1")
SHARED_KEY = b"out-of-band-provisioned-secret"
DECLARATION_REF = f"declaration_{GAME_ID}.json"

PROFILES = InteropProfileSet(
    SeriesConvention.FIXED_ROLE,
    AuthProfile.HMAC_SHA256,
    KEY_ID,
    CommitmentCodec.STRICT_PROJECT_COMMITMENT,
    ResultProfile.STRICT_PROJECT_RESULT,
    CompatibilityProfile.STRICT_COUNTED_MATCH_TURN_OUTCOME_V1,
    ToolNameProfile.PROJECT_LOGICAL_OPERATIONS,
    CanonicalizationProfile.CANONICAL_JSON_V1,
    SealedRecordProfile.SEALED_RECORD_V1,
    StateRepresentationProfile.SEALED_STATE_V1,
    NonceRepresentationProfile.LOWER_HEX_32,
)

PARTICIPANTS = ResultParticipants(GROUP_A, GROUP_B)
LINKS = GithubLinks("https://x/a/p", "https://x/a/t", "https://x/b/p", "https://x/b/t")
CUMULATIVE = CumulativeResult(120, 30, "group_a_lead")
LINES = tuple(SubGameOutcomeLine(i, 20, 5, Outcome.CAPTURE) for i in range(1, 7))


def team(group_id: str, commit: GitCommitSha, *, vram: int | None = 12) -> TeamDeclaration:
    """Return one participant subtree; `vram=None` pairs with no GPU."""
    return TeamDeclaration(
        group_id,
        f"{group_id} team",
        ("first member",),
        RepositoryLinks(f"https://x/{group_id}/pol", f"https://x/{group_id}/thf"),
        f"https://{group_id}.example/mcp",
        HardwareDeclaration("Linux", 8, Decimal("3.5"), 32, "RTX 4090" if vram else False, vram),
        "claude-opus",
        "1.0.0",
        commit,
    )


def partial(
    group_id: str, commit: GitCommitSha, slot: str, *, vram: int | None = 12
) -> Declaration:
    """Return a pre-exchange snapshot carrying exactly one subtree."""
    subtree = team(group_id, commit, vram=vram)
    teams = DeclarationTeams(
        subtree if slot == "group_a" else None,
        subtree if slot == "group_b" else None,
    )
    return Declaration(GAME_ID, GAME_UID, 200000, DeclarationTimes(START, None), teams)


def merged() -> Declaration:
    """Return the post-exchange snapshot carrying both subtrees."""
    teams = DeclarationTeams(team(GROUP_A, COMMIT_A), team(GROUP_B, COMMIT_B))
    return Declaration(GAME_ID, GAME_UID, 200000, DeclarationTimes(START, None), teams)


def config() -> NegotiatedConfig:
    """Return the Appendix-F conforming config; vary it with `dataclasses.replace`."""
    return NegotiatedConfig(
        "mars777-1",
        (GROUP_A, GROUP_B),
        BoardAndAgentsTerms(7, 2, Position(3, 3), Position(0, 0), "top-left", 0),
        WorldTerms("New York", 15),
        MovementAndBarrierTerms(("N", "S", "E", "W", "STAY"), 14, 35, 35),
        ScoringTerms(20, 5, 5, 10, 2, 0),
        PheromoneTerms(Decimal("0.9"), Decimal("0.10"), 5),
        NetworkAndLeagueTerms(30, 60, 6, 10, 2, 10, 200000),
        RateLimiterTerms(30, 2, 5, 3, 100),
    )


def contribution(group_id: str, commit: GitCommitSha, base: int = 100) -> ResultContribution:
    """Return one participant's six-entry contribution."""
    return ResultContribution(
        group_id,
        tuple(ResultContributionEntry(i, commit, base + i) for i in range(1, 7)),
    )


class FixedClock:
    """A deterministic `TimestampPort`; no test ever reads a wall clock."""

    def __init__(self, stamp: UtcTimestamp = STAMP) -> None:
        self.stamp = stamp

    def now(self) -> UtcTimestamp:
        """Return the fixed instant."""
        return self.stamp
