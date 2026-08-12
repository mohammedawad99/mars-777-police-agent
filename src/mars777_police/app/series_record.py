"""Deriving the series-level result facts from the six recorded sub-games.

Nothing here is supplied by a caller that could disagree with the record: the
score comes from `domain.scoring`, the cumulative totals from the six lines, the
played commit from the declaration, the four links from the two declared teams,
and the tokens from the ledger that metered them. A caller can decide *when* to
ask; it cannot decide what the answer is.

**Exactly six, ascending, once each.** `require_complete` is the one gate: a gap
means the series has not been played out, a repeat means one sub-game was
recorded twice, and a seventh cannot exist. Everything below it may therefore
assume a complete record instead of re-checking it.
"""

from ..domain.scoring import score_for
from ..domain.terminal import Outcome
from .declaration_values import Declaration
from .protocol_errors import LocalDefectError
from .result_core_runtime import SubGameOutcomeLine
from .result_core_values import CumulativeResult
from .result_identity_values import GithubLinks
from .result_values import ResultContribution, ResultContributionEntry
from .team_declaration_values import TeamDeclaration
from .token_accounting import TokenAccountingPort

SERIES_LENGTH = 6
"""App F: `num_games` is FIXED at six, so a complete record is exactly six lines."""


def own_team(declaration: Declaration, group_id: str) -> TeamDeclaration:
    """The declared team *group_id* is, without reaching for an attribute by name.

    Both slots are examined rather than selected: a slot the peer has not filled
    is simply not this participant, so there is no unreachable "the slot I chose
    was empty" branch to leave untested.
    """
    for team in (declaration.teams.group_a, declaration.teams.group_b):
        if team is not None and team.group_id == group_id:
            return team
    raise LocalDefectError(f"{group_id!r} has not declared into this game")


def links_of(declaration: Declaration) -> GithubLinks:
    """The four repository links, read from the two teams that declared them."""
    group_a, group_b = declaration.teams.group_a, declaration.teams.group_b
    if group_a is None or group_b is None:
        raise LocalDefectError("the four GitHub links need a merged declaration")
    return GithubLinks(
        group_a.repos.police, group_a.repos.thief, group_b.repos.police, group_b.repos.thief
    )


def outcome_line(sub_game: int, outcome: Outcome) -> SubGameOutcomeLine:
    """One recorded sub-game, scored by the domain table and never by hand."""
    score = score_for(outcome)
    return SubGameOutcomeLine(sub_game, score.cop, score.thief, outcome)


def require_complete(lines: tuple[SubGameOutcomeLine, ...]) -> tuple[SubGameOutcomeLine, ...]:
    """Return *lines* once they are the whole series: six, ascending, once each."""
    played = tuple(line.sub_game for line in lines)
    if played != tuple(range(1, SERIES_LENGTH + 1)):
        raise LocalDefectError(
            f"a series result needs sub-games 1..{SERIES_LENGTH} recorded once each, got {played}",
        )
    return lines


def cumulative_of(lines: tuple[SubGameOutcomeLine, ...]) -> CumulativeResult:
    """Totals derived from the six lines, plus the side they favour.

    `series_outcome` is a validated free string: no live contract closes its
    vocabulary, so the totals decide it and nothing invents a new enum.
    """
    require_complete(lines)
    cop = sum(line.cop_score for line in lines)
    thief = sum(line.thief_score for line in lines)
    if cop == thief:
        return CumulativeResult(cop, thief, "tie")
    return CumulativeResult(cop, thief, "cop" if cop > thief else "thief")


def contribution_of(
    declaration: Declaration,
    group_id: str,
    lines: tuple[SubGameOutcomeLine, ...],
    tokens: TokenAccountingPort,
) -> ResultContribution:
    """Our own six entries: the declared commit, and what each sub-game cost.

    The commit is the one this participant declared for the whole game, restated
    per sub-game exactly as `RESULT_CONTRACT.md` requires - it is never re-read
    from Git mid-series, and it cannot differ between two sub-games.
    """
    commit = own_team(declaration, group_id).github_commit
    return ResultContribution(
        group_id,
        tuple(
            ResultContributionEntry(line.sub_game, commit, tokens.usage(line.sub_game))
            for line in require_complete(lines)
        ),
    )
