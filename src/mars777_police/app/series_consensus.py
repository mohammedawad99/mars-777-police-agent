"""The bytes two teams hash to agree one finished series, and the digest over them.

The settlement is a **two-way** exchange: each side sends its own envelope and
accepts the other's only when the digests match. Receiving without sending is
not half a settlement - it is none, because the peer waits out its whole window
and then records the series as unsettled.

**The scope is everything two honest teams must agree on and nothing they may
legitimately differ on.** A whole result document is per-side by construction -
its own timestamps, its own token counts, its own commit - so hashing that could
never produce equal digests on both sides. What is hashed is
`{game_id, aggregate, sub_games}` with five keys in the aggregate and five per
row; `tie` is deliberately not among the row keys, being derivable from
`winner_group` and already counted in the aggregate.

**The canonical form here is the spaced one**, `sort_keys=True` with Python's
default separators - *not* the compact commitment codec. The two forms are both
"canonical JSON" and produce different bytes for the same object, so mixing them
yields a digest that looks perfectly well-formed and agrees with nobody. This
form is the one a real settlement was reached on.

A tie awards `TIE_SCORE` to both sides, which is why `total_score` can differ
from the sum of the rows and must be computed rather than added up.
"""

import hashlib
import json
from collections.abc import Mapping, Sequence
from typing import Any, Final

from .protocol_errors import LocalDefectError

CLAIM: Final[str] = "series_consensus"
"""The `result_claim` a settlement rides under. Never a sub-game outcome."""

AGGREGATE_KEYS: Final[tuple[str, ...]] = (
    "total_score",
    "sub_games_won",
    "ties",
    "winner_group",
    "series_tie",
)
ROW_KEYS: Final[tuple[str, ...]] = (
    "sub_game_number",
    "roles",
    "result",
    "winner_group",
    "score",
)
SUB_GAMES: Final[int] = 6
TIE_SCORE: Final[int] = 2
"""Appendix F: a tied series awards both groups two points."""


def consensus_scope(
    game_id: str, rows: Sequence[Mapping[str, Any]], ours: str, theirs: str
) -> dict[str, Any]:
    """The agreeable part of a finished series, in the shape both teams hash."""
    if ours == theirs:
        raise LocalDefectError("a series is settled between two distinct groups")
    ordered = _ordered(rows)
    totals = {ours: 0, theirs: 0}
    won = {ours: 0, theirs: 0}
    trimmed: list[dict[str, Any]] = []
    for row in ordered:
        score = {group: int(row["score"][group]) for group in (ours, theirs)}
        totals[ours] += score[ours]
        totals[theirs] += score[theirs]
        winner = _winner(score, ours, theirs)
        if winner is not None:
            won[winner] += 1
        trimmed.append(
            {
                "sub_game_number": int(row["sub_game_number"]),
                "roles": dict(row["roles"]),
                "result": str(row["result"]),
                "winner_group": winner,
                "score": score,
            }
        )
    return {
        "game_id": game_id,
        "aggregate": _aggregate(totals, won, trimmed, ours, theirs),
        "sub_games": [{key: row[key] for key in ROW_KEYS} for row in trimmed],
    }


def _ordered(rows: Sequence[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
    """The six rows, in sub-game order, or a refusal naming what is wrong."""
    if len(rows) != SUB_GAMES:
        raise LocalDefectError(f"a series settles on {SUB_GAMES} sub-games, got {len(rows)}")
    numbers = sorted(int(row["sub_game_number"]) for row in rows)
    if numbers != list(range(1, SUB_GAMES + 1)):
        raise LocalDefectError(f"sub-games must be 1..{SUB_GAMES}, got {numbers}")
    return sorted(rows, key=lambda row: int(row["sub_game_number"]))


def _winner(score: Mapping[str, int], ours: str, theirs: str) -> str | None:
    """Which group took a row, or `None` when the row was drawn."""
    if score[ours] > score[theirs]:
        return ours
    if score[theirs] > score[ours]:
        return theirs
    return None


def _aggregate(
    totals: Mapping[str, int],
    won: Mapping[str, int],
    rows: Sequence[Mapping[str, Any]],
    ours: str,
    theirs: str,
) -> dict[str, Any]:
    """The five-key standing, with the tie award applied where it applies."""
    tied = totals[ours] == totals[theirs]
    awarded = {group: total + TIE_SCORE for group, total in totals.items()} if tied else totals
    return {
        "total_score": dict(awarded),
        "sub_games_won": dict(won),
        "ties": sum(row["winner_group"] is None for row in rows),
        "winner_group": None if tied else max(totals, key=lambda g: totals[g]),
        "series_tie": tied,
    }


def consensus_bytes(scope: Mapping[str, Any]) -> bytes:
    """The spaced canonical form both teams digest. Not the commitment codec."""
    return json.dumps(dict(scope), sort_keys=True, ensure_ascii=False).encode("utf-8")


def consensus_sha256(scope: Mapping[str, Any]) -> str:
    """The settlement digest, lowercase hex."""
    return hashlib.sha256(consensus_bytes(scope)).hexdigest()


def settlement_envelope(sender: str, digest: str) -> dict[str, object]:
    """Exactly the four members the peer's exchange reads. No fifth is added."""
    return {"sender": sender, "result_claim": CLAIM, "records": [], "consensus_sha": digest}


def agrees(envelope: Mapping[str, Any], expected_sender: str, digest: str) -> bool:
    """Whether *envelope* is the peer's matching settlement and not something else.

    Every member is checked, not only the digest: an envelope from the wrong
    side, or one carrying records, is a different message that happens to share
    a claim, and accepting it would settle a series on something nobody sent.
    """
    return (
        envelope.get("sender") == expected_sender
        and envelope.get("result_claim") == CLAIM
        and envelope.get("records") == []
        and envelope.get("consensus_sha") == digest
    )
