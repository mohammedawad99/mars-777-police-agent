"""Where a two-process group's fourteen official files are actually assembled.

Each backend plays three sub-games, so neither holds a complete series. The
gateway is the only place both can reach, and this is what it collects into.
The discipline mirrors `SeriesRowCollector` deliberately: a document settles
once, and an incomplete set is refused rather than written as though complete.
"""

import pytest

from mars777_police.app.kit_schedule import SUB_GAMES
from mars777_police.app.official_artifacts import (
    CONFIG,
    LOG,
    PER_SERIES,
    OfficialArtifactCollector,
)
from mars777_police.app.protocol_errors import StaleMessageError

DOCUMENT = {"sub_game": 1, "entries": []}


def full() -> OfficialArtifactCollector:
    collector = OfficialArtifactCollector()
    for number in range(1, SUB_GAMES + 1):
        collector.record(CONFIG, number, {"config": {}, "sub_game": number})
        collector.record(LOG, number, {"entries": [], "sub_game": number})
    return collector


def test_a_complete_series_is_twelve_per_sub_game_documents() -> None:
    """Six configs and six logs. The declaration and result are series-wide."""
    assert PER_SERIES == 12
    assert full().complete


def test_the_two_backends_halves_meet_here() -> None:
    """Odd sub-games from one process, even from the other, one set at the end."""
    collector = OfficialArtifactCollector()
    for number in (1, 3, 5):
        collector.record(CONFIG, number, DOCUMENT)
        collector.record(LOG, number, DOCUMENT)
    assert not collector.complete
    for number in (2, 4, 6):
        collector.record(CONFIG, number, DOCUMENT)
        collector.record(LOG, number, DOCUMENT)
    assert collector.complete


def test_a_document_settles_once() -> None:
    """A duplicate would silently replace a record both sides may have agreed."""
    collector = OfficialArtifactCollector()
    collector.record(LOG, 2, DOCUMENT)
    with pytest.raises(StaleMessageError, match="already contributed; it settles once"):
        collector.record(LOG, 2, {"entries": ["different"]})
    stored = collector.get(LOG, 2)
    assert stored == DOCUMENT, "the first contribution must survive the refusal"


def test_the_two_families_do_not_collide() -> None:
    """A config and a log for the same sub-game are different documents."""
    collector = OfficialArtifactCollector()
    collector.record(CONFIG, 1, {"config": {}})
    collector.record(LOG, 1, {"entries": []})
    assert collector.get(CONFIG, 1) != collector.get(LOG, 1)


def test_an_unknown_family_is_refused() -> None:
    with pytest.raises(StaleMessageError, match="not an official per-sub-game family"):
        OfficialArtifactCollector().record("result", 1, DOCUMENT)


@pytest.mark.parametrize("number", [0, 7, -1, 99])
def test_a_sub_game_outside_the_series_is_refused(number: int) -> None:
    with pytest.raises(StaleMessageError, match="outside a 6-sub-game series"):
        OfficialArtifactCollector().record(LOG, number, DOCUMENT)


def test_a_non_integer_sub_game_is_refused() -> None:
    """`True` is an int to Python; a sub-game number is not a flag."""
    with pytest.raises(StaleMessageError):
        OfficialArtifactCollector().record(LOG, True, DOCUMENT)  # type: ignore[arg-type]


def test_an_empty_document_is_refused() -> None:
    """An empty file is not evidence that a sub-game happened."""
    with pytest.raises(StaleMessageError, match="carries nothing"):
        OfficialArtifactCollector().record(CONFIG, 1, {})


def test_what_is_missing_is_named_not_merely_counted() -> None:
    """An operator has to see which half is late, not just that one is."""
    collector = OfficialArtifactCollector()
    for number in (1, 3, 5):
        collector.record(CONFIG, number, DOCUMENT)
        collector.record(LOG, number, DOCUMENT)
    assert collector.missing == (
        (CONFIG, 2),
        (CONFIG, 4),
        (CONFIG, 6),
        (LOG, 2),
        (LOG, 4),
        (LOG, 6),
    )


def test_an_incomplete_series_is_refused_and_says_what_is_absent() -> None:
    with pytest.raises(StaleMessageError, match="missing 12 of 12 documents"):
        OfficialArtifactCollector().require_complete()


def test_a_complete_series_passes_the_gate() -> None:
    full().require_complete()


def test_a_stored_document_cannot_be_mutated_through_the_collector() -> None:
    """`get` hands back a copy: a caller editing it must not rewrite the record."""
    collector = OfficialArtifactCollector()
    collector.record(LOG, 1, DOCUMENT)
    taken = collector.get(LOG, 1)
    assert taken is not None
    taken["entries"] = ["tampered"]
    assert collector.get(LOG, 1) == DOCUMENT


def test_an_absent_document_reads_as_none_not_as_empty() -> None:
    """ "Never arrived" and "arrived empty" are different facts."""
    assert OfficialArtifactCollector().get(LOG, 4) is None
