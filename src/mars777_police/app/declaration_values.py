"""The one authoritative ``Declaration`` semantic value and its two composites.

A single immutable type whose *instances* represent the frozen lifecycle moments
(`DECLARATION_CONTRACT.md` R14-R1-1): a **partial** producer snapshot carrying
exactly its own subtree, a **merged** snapshot once both Step-0 exchanges have
happened, and a **final** snapshot that additionally carries ``game_end``. Later
moments construct new values; nothing is mutated. There is deliberately **no**
``declaration_state`` member, no phase and no ``sender_id``.

``Declaration`` is declaration **subject data** and owns no authentication:
``Step0DeclarationExchange`` carries the ``AuthProof`` beside it, and the three
``step0_auth`` artifact keys are that proof's serialization. This module also
builds no Step-0 core projection - that is ``protocol.declaration``'s job.
"""

from dataclasses import dataclass

from .artifact_values import UtcTimestamp
from .team_declaration_values import TeamDeclaration


class InvalidDeclarationError(ValueError):
    """Raised when a declaration snapshot is structurally malformed."""


@dataclass(frozen=True, slots=True)
class DeclarationTimes:
    """The declared game start, and the end once it is known.

    ``game_end`` is absent until close - the reason it is excluded from the
    hashed Step-0 core, which is stamped long before it exists.
    """

    game_start: UtcTimestamp
    game_end: UtcTimestamp | None

    def __post_init__(self) -> None:
        if type(self.game_start) is not UtcTimestamp:
            raise InvalidDeclarationError(
                f"game_start must be a UtcTimestamp, got {type(self.game_start).__name__}",
            )
        if self.game_end is not None and type(self.game_end) is not UtcTimestamp:
            raise InvalidDeclarationError(
                f"game_end must be a UtcTimestamp or None, got {type(self.game_end).__name__}",
            )


@dataclass(frozen=True, slots=True)
class DeclarationTeams:
    """The two participant slots, either of which may be unknown pre-exchange.

    ``group_a``/``group_b`` are **positional slots, not an ordering**: neither
    implies a lower group id. A snapshot with neither subtree declares nothing
    and is refused; exactly one is the partial producer snapshot.
    """

    group_a: TeamDeclaration | None
    group_b: TeamDeclaration | None

    def __post_init__(self) -> None:
        for name, value in (("group_a", self.group_a), ("group_b", self.group_b)):
            if value is not None and type(value) is not TeamDeclaration:
                raise InvalidDeclarationError(
                    f"{name} must be a TeamDeclaration or None, got {type(value).__name__}",
                )
        if self.group_a is None and self.group_b is None:
            raise InvalidDeclarationError(
                "at least one participant subtree must be present;"
                " a declaration with neither declares nothing",
            )

    @property
    def is_merged(self) -> bool:
        """True when both participant subtrees are present."""
        return self.group_a is not None and self.group_b is not None


@dataclass(frozen=True, slots=True)
class Declaration:
    """A declaration snapshot at one lifecycle moment."""

    game_id: str
    game_uid: str
    token_budget_per_series: int
    times: DeclarationTimes
    teams: DeclarationTeams

    def __post_init__(self) -> None:
        for name, text in (("game_id", self.game_id), ("game_uid", self.game_uid)):
            if type(text) is not str:
                raise InvalidDeclarationError(
                    f"{name} must be a str, got {type(text).__name__}",
                )
            if not text:
                raise InvalidDeclarationError(f"{name} must be non-empty")
        if type(self.token_budget_per_series) is not int:
            raise InvalidDeclarationError(
                "token_budget_per_series must be an int, got"
                f" {type(self.token_budget_per_series).__name__}",
            )
        if self.token_budget_per_series <= 0:
            raise InvalidDeclarationError(
                f"token_budget_per_series must be > 0, got {self.token_budget_per_series}",
            )
        if type(self.times) is not DeclarationTimes:
            raise InvalidDeclarationError(
                f"times must be a DeclarationTimes, got {type(self.times).__name__}",
            )
        if type(self.teams) is not DeclarationTeams:
            raise InvalidDeclarationError(
                f"teams must be a DeclarationTeams, got {type(self.teams).__name__}",
            )
        if self.times.game_end is not None and not self.teams.is_merged:
            raise InvalidDeclarationError(
                "game_end may appear only once both participant subtrees are present;"
                " a partial pre-exchange snapshot cannot carry a close time",
            )
