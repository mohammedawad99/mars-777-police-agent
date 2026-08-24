"""This group's six participant-owned contribution entries, met at the gateway.

A `ResultContribution` is **authored by one participant** and covers all six
sub-games. This group plays three of them in each of two backend processes, so
neither backend can author it: each owns half the facts and neither sees the
series. They meet here, for the same reason the settled rows do - the gateway is
the only part of the group both backends can reach.

**Only participant-owned facts travel here.** A row already carries the scores
and the outcome, which are *jointly derived*: both peers compute them from the
played sub-game and the locked scoring table, and neither contributes them. What
a participant genuinely owns and the opponent cannot derive is exactly two
things per sub-game - the commit it played from, and the tokens it spent - so
those are what this collects and nothing else.

**Nothing is inferred and nothing is defaulted.** A sub-game with no entry is
absent, not zero: `contribution` refuses an incomplete set rather than padding
it, because a token count nobody reported is not a token count of nobody.
"""

from dataclasses import dataclass, field

from .artifact_values import GitCommitSha
from .declaration_values import Declaration
from .kit_messages import KitRole
from .kit_schedule import SUB_GAMES, owned_by, require_ours
from .protocol_errors import ReportDisagreeError, StaleMessageError
from .result_core_runtime import slot_of
from .result_values import ResultContribution, ResultContributionEntry


def admit(
    declaration: Declaration | None,
    group_id: str,
    first_role: KitRole,
    role: KitRole,
    sub_game: int,
    github_commit: str,
) -> None:
    """Refuse an entry a backend does not own, or a commit it cannot have played.

    Two independent refusals, both from authorities that already exist.
    `require_ours` is the frozen schedule: a role backend that contributed a
    sub-game the alternation gave the other one would be contributing a side it
    does not implement. The commit check is `check_declared_commit`'s rule
    applied at the moment the entry arrives rather than six sub-games later - the
    played commit must be the one **declared for the role that sub-game was
    actually played in**, which alternates with the schedule.

    Refusing here keeps a wrong entry out of the collector entirely, so the
    group's contribution can never be assembled from one.
    """
    require_ours(sub_game, owned_by(first_role, role), role)
    if declaration is None:
        raise StaleMessageError(
            "a contribution entry needs the merged Step-0 declaration; none has arrived",
        )
    team = getattr(declaration.teams, slot_of(declaration, group_id))
    expected = team.github_commits.for_role(role.value)
    if github_commit != expected.value:
        raise ReportDisagreeError(
            f"sub-game {sub_game} was played as {role.value} and must carry the commit"
            f" this group declared for that role; it carries another",
        )


@dataclass(slots=True)
class ContributionCollector:
    """One participant's six `(sub_game, github_commit, tokens)` entries."""

    entries: dict[int, ResultContributionEntry] = field(default_factory=dict)

    def record(self, sub_game: int, github_commit: str, tokens: int) -> None:
        """Keep one backend's entry for a sub-game it actually played.

        A second entry for the same sub-game is refused rather than overwritten,
        exactly as a settled row is: a sub-game is played once, and letting a
        late or duplicated report replace a contributed value would change what
        the result digest covers after both sides had computed it.
        """
        if not 1 <= sub_game <= SUB_GAMES:
            raise StaleMessageError(
                f"sub-game {sub_game} is outside a {SUB_GAMES}-sub-game series",
            )
        if sub_game in self.entries:
            raise StaleMessageError(
                f"sub-game {sub_game} already contributed its entry; it contributes once",
            )
        self.entries[sub_game] = ResultContributionEntry(
            sub_game, GitCommitSha(github_commit), tokens
        )

    @property
    def complete(self) -> bool:
        """Whether both backends have contributed all six entries."""
        return len(self.entries) == SUB_GAMES

    def contribution(self, group_id: str) -> ResultContribution:
        """This group's own contribution, or a refusal naming what is absent.

        Refused rather than padded. An absent entry means a sub-game whose owner
        has not reported, and a contribution completed on its behalf would carry
        a value that participant never authored.
        """
        if not self.complete:
            absent = sorted(set(range(1, SUB_GAMES + 1)) - set(self.entries))
            raise StaleMessageError(
                f"this group cannot contribute a result without sub-games {absent}",
            )
        return ResultContribution(
            group_id, tuple(self.entries[number] for number in range(1, SUB_GAMES + 1))
        )


def accept(
    collector: ContributionCollector,
    declaration: Declaration | None,
    group_id: str,
    first_role: KitRole,
    role: KitRole,
    sub_game: int,
    github_commit: str,
    tokens: int,
) -> None:
    """Admit one entry and keep it, or refuse it without keeping anything."""
    admit(declaration, group_id, first_role, role, sub_game, github_commit)
    collector.record(sub_game, github_commit, tokens)
