"""Shared fixtures for the Stage 9C counted-reporting tests.

One builder set for both halves: what the gateway writes today, and what a
`RESULT_APPROVAL_CORE` needs before it can exist at all.
"""

import json
from pathlib import Path
from typing import Any

from r16_builders import COMMIT_A, COMMIT_B, GROUP_A, GROUP_B, contribution, merged

from mars777_police.app.artifact_values import UtcTimestamp
from mars777_police.app.counted_series_writer import CountedSeriesWriter
from mars777_police.app.kit_messages import KitRole
from mars777_police.app.kit_settled_row import settled_row
from mars777_police.app.official_artifacts import CONFIG, LOG, OfficialArtifactCollector
from mars777_police.app.series_assembly import SeriesParts, assemble
from mars777_police.app.series_result_owner import SeriesResultOwner
from mars777_police.artifact_documents import declaration_document
from mars777_police.domain.terminal import Outcome
from mars777_police.infra.artifacts import JsonArtifactStore

DIGEST = "9b0e173a79212271dea3f3b546591d7f93fe476ef7e7572aca34f8e88bccc142"
STAMP = "2026-08-24T09:00:00Z"

__all__ = [
    "COMMIT_A",
    "COMMIT_B",
    "DIGEST",
    "GROUP_A",
    "GROUP_B",
    "STAMP",
    "both_contributions",
    "contribution",
    "document",
    "merged",
    "parts",
    "rows",
    "stamp",
    "write_set",
    "written",
]


def stamp() -> UtcTimestamp:
    return UtcTimestamp(STAMP)


def rows(count: int = 6) -> tuple[dict[str, Any], ...]:
    """Alternating rows in the shape the real counted series produced."""
    return tuple(
        settled_row(
            sub_game=n,
            ours=GROUP_A,
            theirs=GROUP_B,
            our_role=KitRole.POLICE if n % 2 else KitRole.THIEF,
            outcome=Outcome.SURVIVAL,
        )
        for n in range(1, count + 1)
    )


def both_contributions() -> tuple[Any, Any]:
    """Both participants' own six-entry contributions, as the agreement carries them."""
    return (contribution(GROUP_A, COMMIT_A), contribution(GROUP_B, COMMIT_B, base=200))


def collected() -> OfficialArtifactCollector:
    store = OfficialArtifactCollector()
    for number in range(1, 7):
        store.record(CONFIG, number, {"config": {}, "sub_game": number})
        store.record(LOG, number, {"entries": [], "sub_game": number})
    return store


def parts(*, agreed: str | None = DIGEST) -> SeriesParts:
    settlement = SeriesResultOwner()
    if agreed is not None:
        settlement.settle(agreed)
    return SeriesParts(
        declaration=merged(), collected=collected(), rows=rows(), settlement=settlement
    )


def write_set(root: Path, given: SeriesParts) -> None:
    """Write the fourteen files exactly as the counted gateway writes them today."""
    assemble(
        given,
        CountedSeriesWriter(JsonArtifactStore(root), merged().game_id),
        declaration_document=declaration_document,
        total_tokens={},
        timestamp=STAMP,
    )


def written(root: Path, **changes: Any) -> Path:
    write_set(root, parts(**changes))
    return root / f"result_{merged().game_id}.json"


def document(root: Path) -> dict[str, Any]:
    return dict(json.loads(written(root).read_text(encoding="utf-8")))
