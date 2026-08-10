"""The `RESULT_APPROVAL_CORE` and the played-series values inside it.

The exact membership `RESULT_CONTRACT.md` freezes, and nothing else. **Excluded
by construction** are `result_sha256` (a digest can never sit inside the bytes it
covers), `mutual_agreement` (agreement state, recorded only after the digests
agree) and `reported_by` with every other reporter-local presentation datum -
which is precisely why the two physical result files need not be byte-identical
while this core must be.

These are **local application values, not a peer family**. Nothing here travels
as a semantic message, enters `app.peer_messages` or adds a `FIELD_MATRIX` row:
the only value that crosses to the peer is `ResultAgreement`, and the only value
that comes back is a `Sha256Digest`.

Representation only - no clock, no canonicalization, no hashing and no assembly
from two contributions. `app.result_core_runtime` owns the assembly and
`protocol.result_core` the bytes.
"""

from dataclasses import dataclass

from ..domain.config_model import FIXED_NUM_GAMES
from ..domain.terminal import Outcome
from .artifact_values import UtcTimestamp
from .result_identity_values import (
    GithubLinks,
    ResultParticipants,
    require_result_score,
    require_result_text,
)
from .result_values import (
    SUB_GAME_SEQUENCE,
    InvalidResultValueError,
    ParticipantGitCommits,
    ParticipantTokenUsage,
)


@dataclass(frozen=True, slots=True)
class SubGameResult:
    """One sub-game's jointly agreed line.

    `github_commit` and `tokens` are **participant-scoped**: a scalar whose
    meaning depended on which peer emitted the report was the exact defect that
    made the core impossible to derive jointly. The scores stay role-keyed
    (`cop`/`thief`) because a sub-game's score belongs to a role, not to a
    participant slot - the two vocabularies are deliberately not merged.
    """

    sub_game: int
    cop_score: int
    thief_score: int
    outcome: Outcome
    github_commit: ParticipantGitCommits
    tokens: ParticipantTokenUsage

    def __post_init__(self) -> None:
        if type(self.sub_game) is not int or self.sub_game not in SUB_GAME_SEQUENCE:
            raise InvalidResultValueError(f"sub_game must be within {SUB_GAME_SEQUENCE}")
        require_result_score(self.cop_score, "cop_score")
        require_result_score(self.thief_score, "thief_score")
        if type(self.outcome) is not Outcome:
            raise InvalidResultValueError(
                f"outcome must be an Outcome, got {type(self.outcome).__name__}",
            )
        for name, expected in (
            ("github_commit", ParticipantGitCommits),
            ("tokens", ParticipantTokenUsage),
        ):
            if type(getattr(self, name)) is not expected:
                raise InvalidResultValueError(f"{name} must be a {expected.__name__}")


@dataclass(frozen=True, slots=True)
class CumulativeResult:
    """The series totals and the series outcome label (Ch 9 p.95; LEAGUE-006).

    `series_outcome` stays a validated non-empty `str`: no live contract closes
    its vocabulary, and inventing an enum here would freeze a set the source
    never fixed.
    """

    cop_total: int
    thief_total: int
    series_outcome: str

    def __post_init__(self) -> None:
        require_result_score(self.cop_total, "cop_total")
        require_result_score(self.thief_total, "thief_total")
        require_result_text(self.series_outcome, "series_outcome")


@dataclass(frozen=True, slots=True)
class ResultApprovalCore:
    """Everything `result_sha256` covers - and nothing it must not."""

    game_id: str
    game_uid: str
    declaration_ref: str
    participants: ResultParticipants
    github_links: GithubLinks
    sub_games: tuple[SubGameResult, ...]
    cumulative: CumulativeResult
    total_tokens: ParticipantTokenUsage
    timestamp: UtcTimestamp

    def __post_init__(self) -> None:
        for name in ("game_id", "game_uid", "declaration_ref"):
            require_result_text(getattr(self, name), name)
        for name, expected in (
            ("participants", ResultParticipants),
            ("github_links", GithubLinks),
            ("cumulative", CumulativeResult),
            ("total_tokens", ParticipantTokenUsage),
            ("timestamp", UtcTimestamp),
        ):
            if type(getattr(self, name)) is not expected:
                raise InvalidResultValueError(f"{name} must be a {expected.__name__}")
        if type(self.sub_games) is not tuple:
            raise InvalidResultValueError("sub_games must be a tuple")
        for entry in self.sub_games:
            if type(entry) is not SubGameResult:
                raise InvalidResultValueError("sub_games entries must be SubGameResult")
        if tuple(entry.sub_game for entry in self.sub_games) != SUB_GAME_SEQUENCE:
            raise InvalidResultValueError(
                f"the core must carry exactly {FIXED_NUM_GAMES} sub-games covering"
                f" {SUB_GAME_SEQUENCE} once each in ascending order",
            )
