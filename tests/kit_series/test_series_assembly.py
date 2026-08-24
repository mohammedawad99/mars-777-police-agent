"""Fourteen files becoming one set, and staying silent until they can.

Every part arrives from somewhere different - the declaration from Step-0, each
config and log from whichever backend played that sub-game, the rows from both,
the consensus digest from whichever owned sub-game six. A group mid-series has
parts outstanding by definition, so "not yet" must not look like a fault.
"""

from pathlib import Path

import pytest
from r16_builders import COMMIT_A, GROUP_A, GROUP_B, merged, partial

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


def collected(upto: int = 6) -> OfficialArtifactCollector:
    store = OfficialArtifactCollector()
    for number in range(1, upto + 1):
        store.record(CONFIG, number, {"config": {}, "sub_game": number})
        store.record(LOG, number, {"entries": [], "sub_game": number})
    return store


def rows(count: int = 6) -> list[dict[str, object]]:
    return [
        settled_row(
            sub_game=n,
            ours=GROUP_A,
            theirs=GROUP_B,
            our_role=KitRole.POLICE if n % 2 else KitRole.THIEF,
            outcome=Outcome.SURVIVAL,
        )
        for n in range(1, count + 1)
    ]


def settled(digest: str | None = DIGEST) -> SeriesResultOwner:
    owner = SeriesResultOwner()
    if digest is not None:
        owner.settle(digest)
    return owner


def parts(**changes: object) -> SeriesParts:
    members: dict[str, object] = {
        "declaration": merged(),
        "collected": collected(),
        "rows": rows(),
        "settlement": settled(),
        **changes,
    }
    return SeriesParts(**members)  # type: ignore[arg-type]


def write(root: Path, made: SeriesParts) -> tuple[str, ...] | None:
    return assemble(
        made,
        CountedSeriesWriter(JsonArtifactStore(root), merged().game_id),
        declaration_document=declaration_document,
        total_tokens={GROUP_A: 10, GROUP_B: 11},
        timestamp="2026-08-23T18:45:00Z",
    )


def test_a_complete_series_writes_exactly_fourteen_files(tmp_path: Path) -> None:
    written = write(tmp_path, parts())
    assert written is not None and len(written) == 14
    assert len(sorted(tmp_path.iterdir())) == 14


@pytest.mark.parametrize(
    ("missing", "change"),
    [
        ("declaration", {"declaration": None}),
        ("half a declaration", {"declaration": partial(GROUP_A, COMMIT_A)}),
        ("documents", {"collected": collected(4)}),
        ("rows", {"rows": rows(5)}),
        ("consensus", {"settlement": settled(None)}),
    ],
)
def test_a_series_mid_flight_writes_nothing_and_is_not_an_error(
    tmp_path: Path, missing: str, change: dict[str, object]
) -> None:
    """Not yet is not a fault: every sub-game boundary would otherwise look like one."""
    assert write(tmp_path, parts(**change)) is None
    assert list(tmp_path.iterdir()) == [], f"{missing} absent, yet something was written"


def test_readiness_is_all_four_parts_not_any_of_them() -> None:
    assert parts().ready
    for change in ({"declaration": None}, {"rows": rows(5)}, {"settlement": settled(None)}):
        assert not parts(**change).ready


def test_assembling_twice_produces_the_same_set(tmp_path: Path) -> None:
    """An official artifact is never overwritten; re-assembling is not a fault."""
    made = parts()
    first = write(tmp_path, made)
    second = write(tmp_path, made)
    assert first == second
    assert len(sorted(tmp_path.iterdir())) == 14
