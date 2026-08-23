"""The declaration artifact: written at Step-0 merge, from both halves, once.

It is the only official file produced before any sub-game runs, and the only one
that describes the series rather than a part of it. These tests pin the moment,
the content and the idempotence - and the refusal that matters most, which is
writing a document that describes half a pairing.
"""

import json
from pathlib import Path

import pytest
from r16_builders import COMMIT_A, GROUP_A, GROUP_B, merged, partial

from mars777_police.app.declaration_values import Declaration
from mars777_police.app.protocol_errors import LocalDefectError
from mars777_police.app.series_declaration import SeriesDeclarationWriter
from mars777_police.artifact_documents import declaration_document
from mars777_police.infra.artifacts import JsonArtifactStore


def writer(root: Path) -> SeriesDeclarationWriter:
    return SeriesDeclarationWriter(JsonArtifactStore(root), declaration_document)


def test_the_merged_declaration_is_written_under_the_official_name(tmp_path: Path) -> None:
    made = merged()
    name = writer(tmp_path).write(made)
    assert name == f"declaration_{made.game_id}.json"
    assert (tmp_path / name).exists()


def test_the_artifact_carries_both_participants(tmp_path: Path) -> None:
    """A reader checking role attribution needs the opponent's commits too."""
    live = writer(tmp_path)
    name = live.write(merged())
    document = json.loads((tmp_path / name).read_text(encoding="utf-8"))
    teams = document["teams"]
    assert teams.get("group_a") is not None
    assert teams.get("group_b") is not None


def test_our_own_half_is_refused(tmp_path: Path) -> None:
    """Writing the pre-merge document would validate and describe half a pairing."""
    with pytest.raises(LocalDefectError, match="half a pairing"):
        writer(tmp_path).write(partial(GROUP_A, COMMIT_A))
    assert list(tmp_path.iterdir()) == []


def test_a_redelivered_step0_does_not_rewrite_it(tmp_path: Path) -> None:
    """The peer retries; the artifact is written once and stays written."""
    live = writer(tmp_path)
    first = live.write(merged())
    second = live.write(merged())
    assert first == second
    assert len(sorted(tmp_path.iterdir())) == 1


def test_nothing_is_written_before_a_merge_arrives(tmp_path: Path) -> None:
    live = writer(tmp_path)
    assert live.written is None
    assert list(tmp_path.iterdir()) == []


def test_the_written_name_is_recorded_for_the_series_writer(tmp_path: Path) -> None:
    """The fourteen-file writer needs to know this one is already on disk."""
    live = writer(tmp_path)
    name = live.write(merged())
    assert live.written == name


def test_the_document_round_trips_as_the_declaration_it_came_from(tmp_path: Path) -> None:
    """Not a summary: what a reader finds is the declaration Step-0 merged."""
    made: Declaration = merged()
    live = writer(tmp_path)
    name = live.write(made)
    document = json.loads((tmp_path / name).read_text(encoding="utf-8"))
    assert document["game_id"] == made.game_id
    assert document["game_uid"] == made.game_uid
    seated = {document["teams"][slot]["group_id"] for slot in ("group_a", "group_b")}
    assert seated == {GROUP_A, GROUP_B}, (
        "a slot orders identifiers and is not one: both participants must appear"
        " whichever slot the deterministic rule gave each"
    )
