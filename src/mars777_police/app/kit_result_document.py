"""The result artifact, from the six rows both sides actually settled on.

The counted `ResultExchange` builds this from its own agreement round. The
reference wire reaches the same fact by a different route: six settled rows, a
consensus digest each side computes independently, and a bidirectional exchange
that completes only when the two match. That agreement is what a result artifact
attests, so it is what this renders.

**Written only against a matching digest.** Rule 35 scores a series with no
agreed result 0 for both groups, so a result file is the one artifact that must
never be produced optimistically. The digest is passed in rather than recomputed
here: recomputing it would let this module agree with itself.

**Role totals, not group totals.** `cumulative` counts what the police side and
the thief side scored across the series, which is a different axis from the
per-group standing the consensus aggregate carries. Both are derived from the
same rows, so neither is guessed - but conflating them would report one number
under the other's name.
"""

from collections.abc import Mapping, Sequence
from typing import Any

from .artifact_store import ArtifactDocument, declaration_name
from .kit_messages import KitRole
from .kit_schedule import SUB_GAMES
from .protocol_errors import LocalDefectError

Row = Mapping[str, Any]


def role_totals(rows: Sequence[Row]) -> tuple[int, int]:
    """What the police side and the thief side scored across the whole series."""
    cop = thief = 0
    for row in rows:
        roles, score = row["roles"], row["score"]
        for group, played in roles.items():
            if played == KitRole.POLICE.value:
                cop += int(score[group])
            else:
                thief += int(score[group])
    return cop, thief


def series_outcome_of(cop: int, thief: int) -> str:
    """The side the totals favour, or a tie. No enum is invented here."""
    if cop == thief:
        return "tie"
    return "cop" if cop > thief else "thief"


def kit_result_document(
    *,
    game_id: str,
    game_uid: str,
    rows: Sequence[Row],
    participants: Sequence[str],
    github_links: Mapping[str, Any],
    total_tokens: Mapping[str, int],
    timestamp: str,
    consensus_sha256: str,
    peer_consensus_sha256: str | None,
) -> ArtifactDocument:
    """Render the official result, or refuse a series that agreed on nothing."""
    if len(rows) != SUB_GAMES:
        raise LocalDefectError(
            f"a result covers {SUB_GAMES} settled rows; this series has {len(rows)}",
        )
    if peer_consensus_sha256 is None:
        raise LocalDefectError(
            "the result artifact waits for the peer's matching consensus;"
            " a series with no agreed result is scored 0 for both groups",
        )
    if peer_consensus_sha256 != consensus_sha256:
        raise LocalDefectError(
            "the peer settled on a different digest; this series agreed on nothing",
        )
    cop, thief = role_totals(rows)
    ordered = sorted(rows, key=lambda row: int(row["sub_game_number"]))
    document: dict[str, Any] = {
        "game_id": game_id,
        "game_uid": game_uid,
        "declaration_ref": declaration_name(game_id),
        "teams": sorted(participants),
        "github_links": dict(github_links),
        "sub_games": [dict(row) for row in ordered],
        "cumulative": {
            "cop_total": cop,
            "thief_total": thief,
            "series_outcome": series_outcome_of(cop, thief),
        },
        "total_tokens": dict(total_tokens),
        "timestamp": timestamp,
        "series_consensus_sha256": consensus_sha256,
    }
    return document
