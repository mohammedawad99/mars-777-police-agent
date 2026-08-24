"""Where the series-wide artifacts are assembled, and why it is not a backend.

The declaration and the result describe the series; the configs and logs
describe its parts. A two-process group has no single backend that sees the
whole series - each plays three sub-games - so the parts travel to the gateway
and the whole is assembled there, beside the rows that were already meeting
there for exactly this reason.

**The backend reports the agreement; it does not render the result.** Whichever
backend owns sub-game six is the one that reaches a matching consensus digest
with the peer, and that fact is what it hands over. Rendering the result needs
the merged declaration - repository links, both participants - which only the
gateway holds, having received Step-0. Passing the declaration down to a backend
so it could render its own copy would give two processes two chances to disagree
about one file.

**The digest is carried, never recomputed here.** It was agreed with the peer;
recomputing it locally would mean this module agreeing with itself, which is the
one thing a settlement must not do.
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from .declaration_values import Declaration
from .kit_result_document import kit_result_document
from .protocol_errors import LocalDefectError, StaleMessageError


@dataclass(slots=True)
class SeriesResultOwner:
    """The group's agreed consensus digest, and the result it licenses."""

    agreed: str | None = field(default=None)
    """The digest both sides settled on, or `None` while none has been reached."""

    def settle(self, consensus_sha256: str) -> None:
        """Record the digest the g06 owner agreed with the peer.

        A second, differing digest is refused rather than overwritten: one series
        settles once, and silently replacing it would let a late report change a
        result both sides already agreed.
        """
        if type(consensus_sha256) is not str or len(consensus_sha256) != 64:
            raise StaleMessageError("a series consensus digest is 64 hex characters")
        if self.agreed is not None and self.agreed != consensus_sha256:
            raise StaleMessageError(
                f"this series already settled on {self.agreed}; it settles once",
            )
        self.agreed = consensus_sha256

    def result(
        self,
        *,
        declaration: Declaration,
        rows: Sequence[Mapping[str, Any]],
        total_tokens: Mapping[str, int],
        timestamp: str,
    ) -> dict[str, Any]:
        """Render the official result, or refuse a series that agreed on nothing."""
        if self.agreed is None:
            raise LocalDefectError(
                "no backend has reported a matching consensus;"
                " a series with no agreed result is scored 0 for both groups",
            )
        teams = declaration.teams
        if not teams.is_merged:
            raise LocalDefectError("the result names both participants; this declaration has one")
        participants = [
            team.group_id for team in (teams.group_a, teams.group_b) if team is not None
        ]
        links = {
            team.group_id: {"police": team.repos.police, "thief": team.repos.thief}
            for team in (teams.group_a, teams.group_b)
            if team is not None
        }
        return dict(
            kit_result_document(
                game_id=declaration.game_id,
                game_uid=declaration.game_uid,
                rows=rows,
                participants=participants,
                github_links=links,
                total_tokens=total_tokens,
                timestamp=timestamp,
                consensus_sha256=self.agreed,
                peer_consensus_sha256=self.agreed,
            )
        )
