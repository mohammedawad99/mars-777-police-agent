"""The result-specific semantic values a peer contributes and the core shares.

Two shapes live here (`RESULT_CONTRACT.md` §R13-R1-1/-3). The **participant-scoped
pairs** are what the shared approval core holds wherever a semantic is
participant-owned - a scalar whose meaning depends on which peer emitted the
report is forbidden inside a document both peers must build identically. The
**contribution** is the sender-owned half that no opponent can derive, carried in
`ResultAgreement` so the other side can build that same core.

**Representation only.** Nothing here canonicalizes, hashes, computes
``result_sha256``, derives ``total_tokens``, reads a clock or talks to a peer.
Reported token counts are exactly that - reported; proving every LLM call was
metered is `TOKEN-ACCOUNTING-CRYPTO-EVIDENCE`, still unfrozen.
"""

from dataclasses import dataclass
from typing import Final

from ..domain.config_model import FIRST_SUB_GAME, FIXED_NUM_GAMES
from .artifact_values import GitCommitSha

SUB_GAME_SEQUENCE: Final[tuple[int, ...]] = tuple(
    range(FIRST_SUB_GAME, FIRST_SUB_GAME + FIXED_NUM_GAMES)
)
"""The exact ascending sub-game sequence a contribution must cover: 1…6."""


class InvalidResultValueError(ValueError):
    """Raised when a result semantic value is structurally malformed."""


def _require_type(value: object, name: str, expected: type) -> None:
    if type(value) is not expected:
        raise InvalidResultValueError(
            f"{name} must be a {expected.__name__}, got {type(value).__name__}",
        )


def _require_token_count(value: object, name: str) -> None:
    if type(value) is not int:
        raise InvalidResultValueError(f"{name} must be an int, got {type(value).__name__}")
    if value < 0:
        raise InvalidResultValueError(f"{name} must be >= 0, got {value}")


@dataclass(frozen=True, slots=True)
class ParticipantGitCommits:
    """Both participants' exact played commit for one sub-game.

    Keyed by the stable participant **slots**, never by role: which side is
    police in a given sub-game follows the series convention and would make the
    ownership of a commit ambiguous.
    """

    group_a: GitCommitSha
    group_b: GitCommitSha

    def __post_init__(self) -> None:
        _require_type(self.group_a, "group_a", GitCommitSha)
        _require_type(self.group_b, "group_b", GitCommitSha)


@dataclass(frozen=True, slots=True)
class ParticipantTokenUsage:
    """Both participants' reported token usage.

    One type serves ``sub_games[].tokens`` and ``total_tokens`` because the
    frozen representation is identical; the series total is **derived** from the
    six sub-game values, so no combined field exists and none is added.
    """

    group_a: int
    group_b: int

    def __post_init__(self) -> None:
        _require_token_count(self.group_a, "group_a")
        _require_token_count(self.group_b, "group_b")


@dataclass(frozen=True, slots=True)
class ResultContributionEntry:
    """One sub-game of a single participant's sender-owned contribution."""

    sub_game: int
    github_commit: GitCommitSha
    tokens: int

    def __post_init__(self) -> None:
        if type(self.sub_game) is not int:
            raise InvalidResultValueError(
                f"sub_game must be an int, got {type(self.sub_game).__name__}",
            )
        if self.sub_game not in SUB_GAME_SEQUENCE:
            raise InvalidResultValueError(
                f"sub_game must be within {SUB_GAME_SEQUENCE}, got {self.sub_game}",
            )
        _require_type(self.github_commit, "github_commit", GitCommitSha)
        _require_token_count(self.tokens, "tokens")


@dataclass(frozen=True, slots=True)
class ResultContribution:
    """Everything one participant owns that the opponent cannot derive.

    Exactly six entries covering 1…6 in ascending order - never sorted, never
    deduplicated, never repaired. The six commits must be **equal**: the played
    commit is fixed for the game (Ch 5 permits change *between* games and the
    declaration is per-game), so six differing values inside one immutable
    contribution are self-contradictory before any peer is consulted. Comparing
    that commit against the actual `Declaration` is a LIVE duty, not this value's.
    """

    group_id: str
    entries: tuple[ResultContributionEntry, ...]

    def __post_init__(self) -> None:
        if type(self.group_id) is not str:
            raise InvalidResultValueError(
                f"group_id must be a str, got {type(self.group_id).__name__}",
            )
        if not self.group_id:
            raise InvalidResultValueError("group_id must be non-empty")
        if type(self.entries) is not tuple:
            raise InvalidResultValueError(
                f"entries must be a tuple, got {type(self.entries).__name__}",
            )
        for entry in self.entries:
            _require_type(entry, "entry", ResultContributionEntry)
        if tuple(entry.sub_game for entry in self.entries) != SUB_GAME_SEQUENCE:
            raise InvalidResultValueError(
                f"entries must cover sub-games {SUB_GAME_SEQUENCE} exactly once each in"
                " ascending order; they are never sorted, deduplicated or repaired",
            )
        commits = {entry.github_commit for entry in self.entries}
        if len(commits) != 1:
            raise InvalidResultValueError(
                "every entry must carry the same github_commit: a participant's played"
                " commit is fixed for the whole game",
            )
