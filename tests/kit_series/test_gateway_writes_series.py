"""The gateway writing fourteen files the moment the last part arrives.

Every component was unit-tested and none of them was invoked: a local rehearsal
played six sub-games, collected all twelve documents at the gateway, and wrote
two development files because nothing called the assembler. A writer nothing
calls is not a record, exactly as a guard nothing calls is not a guard.

So these drive the gateway's own contribution methods - the ones the backends
actually call over the admin surface - and assert on what reaches disk.
"""

from pathlib import Path

from r16_builders import GROUP_A, GROUP_B, merged

from mars777_police.app.counted_mode import counted, rehearsal
from mars777_police.app.counted_series_writer import CountedSeriesWriter
from mars777_police.app.kit_handoff import SeriesHandoff
from mars777_police.app.kit_messages import KitRole
from mars777_police.app.kit_settled_row import settled_row
from mars777_police.app.official_artifacts import CONFIG, LOG
from mars777_police.app.series_assembly import SeriesParts, assemble
from mars777_police.artifact_documents import declaration_document
from mars777_police.domain.terminal import Outcome
from mars777_police.infra.artifacts import JsonArtifactStore
from mars777_police.transport.kit_gateway import KitGroupGateway

DIGEST = "9b0e173a79212271dea3f3b546591d7f93fe476ef7e7572aca34f8e88bccc142"


def writer(root: Path):
    store = CountedSeriesWriter(JsonArtifactStore(root), merged().game_id)

    def write(parts: SeriesParts) -> tuple[str, ...] | None:
        return assemble(
            parts,
            store,
            declaration_document=declaration_document,
            total_tokens={},
            timestamp="2026-08-24T09:00:00Z",
        )

    return write


def gateway(root: Path, *, is_counted: bool = True) -> KitGroupGateway:
    return KitGroupGateway(
        handoff=SeriesHandoff(KitRole.POLICE),
        routes={},
        deadline=30.0,
        counted=counted() if is_counted else rehearsal(),
        write=writer(root),
        declaration=merged(),
    )


def feed(live: KitGroupGateway, *, rows: int = 6, documents: int = 6) -> None:
    """Everything the two backends contribute, in an order neither controls."""
    for number in range(1, documents + 1):
        live.contribute_artifact(CONFIG, number, {"config": {}, "sub_game": number})
        live.contribute_artifact(LOG, number, {"entries": [], "sub_game": number})
    for number in range(1, rows + 1):
        live.contribute(
            settled_row(
                sub_game=number,
                ours=GROUP_A,
                theirs=GROUP_B,
                our_role=KitRole.POLICE if number % 2 else KitRole.THIEF,
                outcome=Outcome.SURVIVAL,
            )
        )


def test_the_series_is_written_when_the_last_part_lands(tmp_path: Path) -> None:
    """The settlement digest arrives last here, and writing follows it."""
    live = gateway(tmp_path)
    feed(live)
    assert list(tmp_path.iterdir()) == [], "nothing may be written before consensus"
    live.series_settled(DIGEST)
    assert len(sorted(tmp_path.iterdir())) == 14


def test_the_order_the_parts_arrive_in_does_not_matter(tmp_path: Path) -> None:
    """Two processes contribute concurrently; neither controls who is last."""
    live = gateway(tmp_path)
    live.series_settled(DIGEST)
    assert list(tmp_path.iterdir()) == [], "a digest alone is not a series"
    feed(live)
    assert len(sorted(tmp_path.iterdir())) == 14


def test_a_series_still_missing_a_part_writes_nothing(tmp_path: Path) -> None:
    live = gateway(tmp_path)
    feed(live, rows=5, documents=6)
    live.series_settled(DIGEST)
    assert list(tmp_path.iterdir()) == []


def test_a_rehearsal_writes_no_official_set(tmp_path: Path) -> None:
    """The official set is a counted artefact; a rehearsal producing one would
    be the record of a game that does not count."""
    live = gateway(tmp_path, is_counted=False)
    feed(live)
    live.series_settled(DIGEST)
    assert list(tmp_path.iterdir()) == []


def test_a_gateway_with_no_writer_collects_but_writes_nothing(tmp_path: Path) -> None:
    live = KitGroupGateway(
        handoff=SeriesHandoff(KitRole.POLICE), routes={}, deadline=30.0, counted=counted()
    )
    feed(live)
    live.series_settled(DIGEST)
    assert live.artifacts.complete
    assert list(tmp_path.iterdir()) == []


def test_writing_twice_is_idempotent(tmp_path: Path) -> None:
    """Every contribution asks; an official artifact is never overwritten."""
    live = gateway(tmp_path)
    feed(live)
    live.series_settled(DIGEST)
    live.series_settled(DIGEST)
    assert len(sorted(tmp_path.iterdir())) == 14
