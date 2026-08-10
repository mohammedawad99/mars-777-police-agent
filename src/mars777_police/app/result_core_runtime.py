"""Assembling the one `RESULT_APPROVAL_CORE` both peers must build identically.

The merge is deliberately **independent of who performs it**: for every sub-game
and each participant slot, that slot's contributed commit and token count are
placed in the participant-scoped object by a fixed rule. Dependence on the
assembler was precisely the defect that made the core non-derivable before, so
nothing here consults "our" side or a role.

`total_tokens` is **derived**, never transmitted: each participant's total is the
sum of its six contributed sub-game values, so one semantic fact has exactly one
representation and a separately reported total cannot contradict its parts.

Slots come from the merged `Declaration`, the only authority on which participant
occupies `group_a`. A contribution's `group_id` **selects** a slot; it never
defines one. Police and thief are never used as participant ownership - roles
alternate across a series, participants do not.

Contributed token counts are what a peer **reported**. Nothing here, and nothing
downstream, treats them as verified provider consumption
(`TOKEN-ACCOUNTING-CRYPTO-EVIDENCE: BLOCKED-BY-CONSTRUCTION`).
"""

from dataclasses import dataclass

from ..domain.terminal import Outcome
from .artifact_values import UtcTimestamp
from .declaration_values import Declaration
from .protocol_errors import LocalDefectError, ReportDisagreeError
from .result_core_values import CumulativeResult, ResultApprovalCore, SubGameResult
from .result_identity_values import GithubLinks, ResultParticipants
from .result_values import (
    ParticipantGitCommits,
    ParticipantTokenUsage,
    ResultContribution,
)

PARTICIPANT_SLOTS = ("group_a", "group_b")


@dataclass(frozen=True, slots=True)
class SubGameOutcomeLine:
    """The locally computed half of one sub-game line.

    Scores and outcome are identical on both peers by construction (INV-07) -
    they follow from the played sub-game and the locked scoring table, so they
    are never contributed and never negotiated.
    """

    sub_game: int
    cop_score: int
    thief_score: int
    outcome: Outcome


def participants_of(declaration: Declaration) -> ResultParticipants:
    """Return the two `group_id`s in their declared slots, or refuse a partial."""
    group_a, group_b = declaration.teams.group_a, declaration.teams.group_b
    if group_a is None or group_b is None:
        raise LocalDefectError("the result core needs a merged declaration")
    return ResultParticipants(group_a.group_id, group_b.group_id)


def slot_of(declaration: Declaration, group_id: str) -> str:
    """Return the canonical slot *group_id* occupies in this declaration."""
    for slot in PARTICIPANT_SLOTS:
        team = getattr(declaration.teams, slot)
        if team is not None and team.group_id == group_id:
            return slot
    raise ReportDisagreeError(f"{group_id!r} is not a declared participant of this game")


def check_declared_commit(declaration: Declaration, contribution: ResultContribution) -> None:
    """Refuse a contribution whose commit is not the one that participant declared."""
    team = getattr(declaration.teams, slot_of(declaration, contribution.group_id))
    for entry in contribution.entries:
        if entry.github_commit != team.github_commit:
            raise ReportDisagreeError(
                f"sub-game {entry.sub_game} contributes a commit that {contribution.group_id!r}"
                " did not declare for this game",
            )


def total_tokens(contribution: ResultContribution) -> int:
    """Return the sum of one participant's six contributed sub-game values."""
    return sum(entry.tokens for entry in contribution.entries)


def by_slot(
    declaration: Declaration,
    contributions: tuple[ResultContribution, ResultContribution],
) -> dict[str, ResultContribution]:
    """Place both contributions in their declared slots, refusing a collision."""
    placed = {slot_of(declaration, item.group_id): item for item in contributions}
    if len(placed) != len(PARTICIPANT_SLOTS):
        raise ReportDisagreeError("both contributions claim the same participant slot")
    return placed


def _line(
    placed: dict[str, ResultContribution],
    index: int,
    line: SubGameOutcomeLine,
) -> SubGameResult:
    first = placed["group_a"].entries[index]
    second = placed["group_b"].entries[index]
    if first.sub_game != line.sub_game or second.sub_game != line.sub_game:
        raise ReportDisagreeError(
            f"contributed entry {index} is not sub-game {line.sub_game}",
        )
    return SubGameResult(
        line.sub_game,
        line.cop_score,
        line.thief_score,
        line.outcome,
        ParticipantGitCommits(first.github_commit, second.github_commit),
        ParticipantTokenUsage(first.tokens, second.tokens),
    )


def assemble(
    declaration: Declaration,
    declaration_ref: str,
    lines: tuple[SubGameOutcomeLine, ...],
    contributions: tuple[ResultContribution, ResultContribution],
    links: GithubLinks,
    cumulative: CumulativeResult,
    timestamp: UtcTimestamp,
) -> ResultApprovalCore:
    """Return the approval core both peers derive from the same inputs."""
    for item in contributions:
        check_declared_commit(declaration, item)
    placed = by_slot(declaration, contributions)
    return ResultApprovalCore(
        declaration.game_id,
        declaration.game_uid,
        declaration_ref,
        participants_of(declaration),
        links,
        tuple(_line(placed, index, line) for index, line in enumerate(lines)),
        cumulative,
        ParticipantTokenUsage(
            total_tokens(placed["group_a"]),
            total_tokens(placed["group_b"]),
        ),
        timestamp,
    )
