"""The `RESULT_APPROVAL_CORE` of an alternating counted series, built at the gateway.

`SeriesDriver` builds this core from a `ResultExchange` because a fixed-role
series is played by one process that sees all six sub-games. An alternating
series is not: this group plays three sub-games in each of two processes and
only the gateway ever holds the whole series, which is why `SeriesResultOwner`
exists at all.

**Nothing here is a second assembly authority.** The join itself belongs to
`app.result_core_runtime.assemble` and stays there: it places both participants'
contributions by declared slot, refuses a commit that is not the one declared
for the role that sub-game was played in, and derives `total_tokens` as the sum
of each participant's own six contributed values. This module only turns the
gateway's settled rows into the locally computed half - the scores and outcome
that follow from the played sub-game and the locked scoring table, which are
never contributed and never negotiated - and hands them over.

**Token counts are participant-owned and are never manufactured here.** Both
participants' six values arrive inside their own `ResultContribution`; there is
no default, no fallback and no substitution for an absent one. A missing or
short peer contribution leaves the result agreement incomplete, which is what
keeps a series nobody agreed from being reported.

`result_sha256` remains `SHA256(canonical_bytes(RESULT_APPROVAL_CORE))`, computed
by `protocol.result_core.ResultDigester`, and stays a different fact from
`series_consensus_sha256`: one covers this core, the other the settlement scope.
"""

from collections.abc import Mapping, Sequence
from typing import Any, Final

from .app.artifact_store import declaration_name
from .app.artifact_values import UtcTimestamp
from .app.declaration_values import Declaration
from .app.kit_messages import KitRole
from .app.kit_result_document import role_totals, series_outcome_of
from .app.participant_slots import PARTICIPANT_SLOTS
from .app.protocol_errors import LocalDefectError
from .app.result_core_runtime import SubGameOutcomeLine, assemble
from .app.result_core_values import CumulativeResult, ResultApprovalCore
from .app.result_identity_values import GithubLinks
from .app.result_values import ResultContribution
from .app.series_roles_source import series_roles_for
from .domain.terminal import Outcome
from .protocol.result_core import OUTCOME_TOKENS

OUTCOME_OF_TOKEN: Final[dict[str, Outcome]] = {
    token: outcome for outcome, token in OUTCOME_TOKENS.items()
}
"""The artifact spelling back to the domain event, inverted from the one table.

Derived from `OUTCOME_TOKENS` rather than written out a second time, so the two
directions cannot drift apart, and unmapped text raises instead of guessing.
"""


def outcome_of(token: str) -> Outcome:
    """Return the domain outcome *token* spells, refusing an unknown word."""
    outcome = OUTCOME_OF_TOKEN.get(token)
    if outcome is None:
        raise LocalDefectError(f"no outcome is frozen for the result spelling {token!r}")
    return outcome


def _team(declaration: Declaration, slot: str) -> Any:
    team = getattr(declaration.teams, slot)
    if team is None:
        raise LocalDefectError("the result core needs a merged declaration")
    return team


def line_of(row: Mapping[str, Any]) -> SubGameOutcomeLine:
    """One sub-game's locally computed half, read by the role actually played."""
    cop = thief = 0
    for group, played in row["roles"].items():
        if played == KitRole.POLICE.value:
            cop = int(row["score"][group])
        else:
            thief = int(row["score"][group])
    return SubGameOutcomeLine(
        int(row["sub_game_number"]), cop, thief, outcome_of(str(row["result"]))
    )


def links_of(declaration: Declaration) -> GithubLinks:
    first, second = (_team(declaration, slot) for slot in PARTICIPANT_SLOTS)
    return GithubLinks(
        first.repos.police, first.repos.thief, second.repos.police, second.repos.thief
    )


def approval_core(
    declaration: Declaration,
    rows: Sequence[Mapping[str, Any]],
    timestamp: UtcTimestamp,
    contributions: tuple[ResultContribution, ResultContribution],
    group_id: str,
) -> ResultApprovalCore:
    """The approval core both peers derive, from both participants' own data.

    *contributions* carries each participant's six `(sub_game, github_commit,
    tokens)` entries, authored and authenticated by that participant. Both are
    required: there is no core to build from one, and none is invented.
    """
    ordered = sorted(rows, key=lambda row: int(row["sub_game_number"]))
    cop, thief = role_totals(ordered)
    return assemble(
        declaration,
        declaration_name(declaration.game_id),
        tuple(line_of(row) for row in ordered),
        contributions,
        links_of(declaration),
        CumulativeResult(cop, thief, series_outcome_of(cop, thief)),
        timestamp,
        series_roles_for(declaration, group_id),
    )
