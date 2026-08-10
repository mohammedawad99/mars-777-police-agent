"""Canonical bytes and `result_sha256` over the result approval core.

`result_sha256 = SHA256(canonical_bytes(RESULT_APPROVAL_CORE))` - **unkeyed** and
**non-self-referential**: the digest is stored outside the bytes it covers, and
`mutual_agreement` and `reported_by` are excluded by the core's own shape rather
than filtered out here. No keyed proof exists for result approval, because the
source requires a SHA-256-backed *mutual acknowledgement*, not producer
authentication.

`outcome` crosses one vocabulary boundary, and it is crossed **explicitly**.
`domain.terminal.Outcome` spells the locked Ch-3 end events `CAPTURE`,
`SURVIVAL` and `TECHNICAL_LOSS`; the result artifact spells them `capture`,
`survival` and `technical_loss`. The mapping is a table, never `lower()` - the
same discipline `"POLICE"` → `"police"` already follows - so an unmapped member
raises instead of being transformed into a guess. The contract's fourth token
`tie` is deliberately **not** produced: Ch 3 Table 2 has no tie end event and
`Outcome` has no `TIE` member, so no sub-game can legitimately carry it and this
module will not invent one.
"""

from hashlib import sha256
from typing import Final

from ..app.protocol_errors import LocalDefectError
from ..app.protocol_values import Sha256Digest
from ..app.result_core_values import ResultApprovalCore, SubGameResult
from ..app.result_identity_values import GithubLinks, ResultParticipants
from ..app.result_values import ParticipantGitCommits, ParticipantTokenUsage
from ..domain.terminal import Outcome
from .canonical import canonical_json_bytes

OUTCOME_TOKENS: Final[dict[Outcome, str]] = {
    Outcome.CAPTURE: "capture",
    Outcome.SURVIVAL: "survival",
    Outcome.TECHNICAL_LOSS: "technical_loss",
}
"""The explicit domain-to-artifact outcome mapping - a table, never a transform."""

GITHUB_LINK_KEYS: Final[tuple[str, ...]] = (
    "group_a_police",
    "group_a_thief",
    "group_b_police",
    "group_b_thief",
)


def outcome_token(outcome: Outcome) -> str:
    """Return the artifact spelling of *outcome*, refusing an unmapped member."""
    token = OUTCOME_TOKENS.get(outcome)
    if token is None:
        raise LocalDefectError(f"no result spelling is frozen for outcome {outcome!r}")
    return token


def _commits(commits: ParticipantGitCommits) -> dict[str, object]:
    return {"group_a": commits.group_a.value, "group_b": commits.group_b.value}


def _tokens(tokens: ParticipantTokenUsage) -> dict[str, object]:
    return {"group_a": tokens.group_a, "group_b": tokens.group_b}


def _participants(participants: ResultParticipants) -> dict[str, object]:
    return {
        "group_a": {"group_id": participants.group_a},
        "group_b": {"group_id": participants.group_b},
    }


def _links(links: GithubLinks) -> dict[str, object]:
    return {key: getattr(links, key) for key in GITHUB_LINK_KEYS}


def _sub_game(entry: SubGameResult) -> dict[str, object]:
    return {
        "sub_game": entry.sub_game,
        "cop_score": entry.cop_score,
        "thief_score": entry.thief_score,
        "outcome": outcome_token(entry.outcome),
        "github_commit": _commits(entry.github_commit),
        "tokens": _tokens(entry.tokens),
    }


def result_core(core: ResultApprovalCore) -> dict[str, object]:
    """Return the canonical JSON-native projection of the approval core."""
    return {
        "game_id": core.game_id,
        "game_uid": core.game_uid,
        "declaration_ref": core.declaration_ref,
        "teams": _participants(core.participants),
        "github_links": _links(core.github_links),
        "sub_games": [_sub_game(entry) for entry in core.sub_games],
        "cumulative": {
            "cop_total": core.cumulative.cop_total,
            "thief_total": core.cumulative.thief_total,
            "series_outcome": core.cumulative.series_outcome,
        },
        "total_tokens": _tokens(core.total_tokens),
        "timestamp": core.timestamp.value,
    }


class ResultDigester:
    """The `ResultDigestPort` adapter: canonical bytes in, one digest out."""

    def digest(self, core: ResultApprovalCore) -> Sha256Digest:
        """Return `result_sha256` for *core*, computed locally and never trusted."""
        return Sha256Digest(sha256(canonical_json_bytes(result_core(core))).hexdigest())
