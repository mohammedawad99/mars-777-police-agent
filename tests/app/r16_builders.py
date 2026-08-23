"""Shared R16 fixtures: two participants and one finished series.

Duplicated per test directory on purpose - `tests/app` and `tests/protocol` have
no package, so each owns the helpers it imports.

`GROUP-XY` is byte-wise **lower** than `MaRs-777`, so the synthetic pairing seats
the opponent in `group_a` and **us in `group_b`** - the mirror of the real
pairing against `s82kma9e`. Fixtures therefore never name a slot: they name the
producing group and let `slot_of` seat it, which is what keeps a test from
quietly encoding one pairing's seating as if it were a rule.
"""

from decimal import Decimal

from r16_config import GROUP_A as GROUP_A
from r16_config import GROUP_B as GROUP_B
from r16_config import config as config

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
from mars777_police.app.participant_slots import slot_of, slots_for
from mars777_police.app.result_core_runtime import SubGameOutcomeLine
from mars777_police.app.result_core_values import CumulativeResult
from mars777_police.app.result_identity_values import GithubLinks, ResultParticipants
from mars777_police.app.result_values import ResultContribution, ResultContributionEntry
from mars777_police.app.team_declaration_values import (
    HardwareDeclaration,
    RepositoryLinks,
    RoleCommits,
    TeamDeclaration,
)
from mars777_police.domain.terminal import Outcome

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
    CompatibilityProfile.STRICT_COUNTED_MATCH_TURN_OUTCOME_SCENT_V2,
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


def team(
    group_id: str,
    commit: GitCommitSha,
    *,
    vram: int | None = 12,
    thief_commit: GitCommitSha | None = None,
) -> TeamDeclaration:
    """Return one participant subtree; `vram=None` pairs with no GPU.

    `commit` is the police-role commit and, by default, the thief-role one too:
    most fixtures predate role-specific commits and only care that a declaration
    exists. `thief_commit` is how a role-aware test says the two differ.
    """
    return TeamDeclaration(
        group_id,
        f"{group_id} team",
        ("first member",),
        RepositoryLinks(f"https://x/{group_id}/pol", f"https://x/{group_id}/thf"),
        f"https://{group_id}.example/mcp",
        HardwareDeclaration("Linux", 8, Decimal("3.5"), 32, "RTX 4090" if vram else False, vram),
        "claude-opus",
        "1.0.0",
        RoleCommits(commit, thief_commit or commit),
    )


def partial(
    group_id: str, commit: GitCommitSha, slot: str | None = None, *, vram: int | None = 12
) -> Declaration:
    """Return a pre-exchange snapshot carrying exactly one subtree.

    `slot` defaults to the one the deterministic rule assigns, so a fixture says
    which group is producing and not where it sits. Passing a slot explicitly is
    how a negative test asserts a wrong layout is refused.
    """
    slot = slot or slot_of(GROUP_A, GROUP_B, group_id)
    subtree = team(group_id, commit, vram=vram)
    teams = DeclarationTeams(
        subtree if slot == "group_a" else None,
        subtree if slot == "group_b" else None,
    )
    return Declaration(GAME_ID, GAME_UID, 200000, DeclarationTimes(START, None), teams)


def _placed(one: TeamDeclaration, two: TeamDeclaration) -> DeclarationTeams:
    """Seat both subtrees by the deterministic slot rule, never by argument order."""
    by_slot = slots_for(one.group_id, two.group_id)
    teams = {t.group_id: t for t in (one, two)}
    return DeclarationTeams(
        by_slot["group_a"] and teams[by_slot["group_a"]],
        by_slot["group_b"] and teams[by_slot["group_b"]],
    )


def merged() -> Declaration:
    """Return the post-exchange snapshot carrying both subtrees."""
    teams = _placed(team(GROUP_A, COMMIT_A), team(GROUP_B, COMMIT_B))
    return Declaration(GAME_ID, GAME_UID, 200000, DeclarationTimes(START, None), teams)


def merged_with_distinct_role_commits() -> Declaration:
    """A snapshot where group A's two repositories declare different commits.

    Most fixtures declare one commit for both roles because they predate role
    alternation. A role-aware refusal can only be observed when the two actually
    differ, which is what this builder exists to say out loud.
    """
    teams = _placed(team(GROUP_A, COMMIT_A, thief_commit=COMMIT_B), team(GROUP_B, COMMIT_B))
    return Declaration(GAME_ID, GAME_UID, 200000, DeclarationTimes(START, None), teams)


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
