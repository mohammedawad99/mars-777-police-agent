"""The fourteen official files: written whole, or not written at all.

A group that writes some of the set has not produced a counted series. These
tests pin the exact count, the exact names, the order, and the two refusals
that matter most - an incomplete set, and a result asserting an agreement that
never happened.
"""

import json
from pathlib import Path

import pytest

from mars777_police.app.counted_series_writer import OFFICIAL_FILES, CountedSeriesWriter
from mars777_police.app.kit_schedule import SUB_GAMES
from mars777_police.app.official_artifacts import CONFIG, LOG, OfficialArtifactCollector
from mars777_police.app.protocol_errors import LocalDefectError
from mars777_police.infra.artifacts import JsonArtifactStore

GAME_ID = "MaRs-777-vs-s82kma9e"
DECLARATION = {"game_id": GAME_ID, "teams": {}}
RESULT = {"game_id": GAME_ID, "result_sha256": "a" * 64}


def collected(upto: int = SUB_GAMES) -> OfficialArtifactCollector:
    store = OfficialArtifactCollector()
    for number in range(1, upto + 1):
        store.record(CONFIG, number, {"config": {}, "sub_game": number})
        store.record(LOG, number, {"entries": [], "sub_game": number})
    return store


def writer(root: Path) -> CountedSeriesWriter:
    return CountedSeriesWriter(JsonArtifactStore(root), GAME_ID)


def test_the_official_set_is_exactly_fourteen(tmp_path: Path) -> None:
    written = writer(tmp_path).write(declaration=DECLARATION, collected=collected(), result=RESULT)
    assert OFFICIAL_FILES == 14
    assert len(written) == 14
    assert len(sorted(tmp_path.iterdir())) == 14


def test_the_names_are_the_four_official_families(tmp_path: Path) -> None:
    written = writer(tmp_path).write(declaration=DECLARATION, collected=collected(), result=RESULT)
    assert written[0] == f"declaration_{GAME_ID}.json"
    assert written[-1] == f"result_{GAME_ID}.json"
    assert sum(name.startswith("config_") for name in written) == SUB_GAMES
    assert sum(name.startswith("log_") for name in written) == SUB_GAMES


def test_each_sub_game_config_precedes_its_own_log(tmp_path: Path) -> None:
    """The order the sub-game produced them, not an arbitrary sort."""
    written = writer(tmp_path).write(declaration=DECLARATION, collected=collected(), result=RESULT)
    for number in range(1, SUB_GAMES + 1):
        token = f"g{number:02d}"
        config_at = written.index(f"config_{GAME_ID}_{token}.json")
        log_at = written.index(f"log_{GAME_ID}_{token}.json")
        assert config_at < log_at


def test_an_incomplete_series_writes_nothing_at_all(tmp_path: Path) -> None:
    """Thirteen files is not a counted series; it is evidence one was attempted."""
    with pytest.raises(Exception, match="missing"):
        writer(tmp_path).write(declaration=DECLARATION, collected=collected(3), result=RESULT)
    assert list(tmp_path.iterdir()) == []


def test_a_series_with_no_agreement_writes_no_result(tmp_path: Path) -> None:
    """Rule 35 scores an unagreed series 0; a result file would be indefensible."""
    with pytest.raises(LocalDefectError, match="waits for a mutual agreement"):
        writer(tmp_path).write(declaration=DECLARATION, collected=collected(), result=None)
    assert list(tmp_path.iterdir()) == []


def test_a_missing_declaration_is_refused(tmp_path: Path) -> None:
    with pytest.raises(LocalDefectError, match="merged declaration"):
        writer(tmp_path).write(declaration={}, collected=collected(), result=RESULT)


def test_the_documents_land_intact(tmp_path: Path) -> None:
    """What the builders produced is what a reader finds, unchanged."""
    writer(tmp_path).write(declaration=DECLARATION, collected=collected(), result=RESULT)
    stored = json.loads((tmp_path / f"result_{GAME_ID}.json").read_text(encoding="utf-8"))
    assert stored == RESULT
    first = json.loads((tmp_path / f"log_{GAME_ID}_g01.json").read_text(encoding="utf-8"))
    assert first == {"entries": [], "sub_game": 1}


def test_writing_the_same_series_twice_is_idempotent(tmp_path: Path) -> None:
    """An official artifact is never overwritten, and rewriting it is not a fault."""
    live = writer(tmp_path)
    first = live.write(declaration=DECLARATION, collected=collected(), result=RESULT)
    second = live.write(declaration=DECLARATION, collected=collected(), result=RESULT)
    assert first == second
    assert len(sorted(tmp_path.iterdir())) == 14
