"""The refusal matrix: every way a counted series can go wrong, failing closed.

Each case here is a way a real series could be corrupted rather than merely
broken - a peer that disagrees, a document that arrives twice, a rehearsal that
tries to report. Individually these refusals are tested where they live; this
suite exists to assert the *set* of them, so a capability added later without a
refusal is visible as a gap in one place rather than absent everywhere.

Every case asserts two things: that it refuses, and that refusing leaves the
valid state it was given untouched. A refusal that corrupts what it guarded is
not fail-closed.
"""

from typing import Any

import pytest

from mars777_police.app.counted_mode import counted, rehearsal
from mars777_police.app.counted_series_writer import CountedSeriesWriter
from mars777_police.app.kit_messages import KitRole
from mars777_police.app.kit_result_document import kit_result_document
from mars777_police.app.kit_series_rows import SeriesRowCollector
from mars777_police.app.kit_settled_row import settled_row
from mars777_police.app.official_artifacts import CONFIG, LOG, OfficialArtifactCollector
from mars777_police.app.protocol_errors import LocalDefectError, StaleMessageError
from mars777_police.domain.terminal import Outcome
from mars777_police.infra.artifacts import JsonArtifactStore

OURS, THEIRS = "MaRs-777", "s82kma9e"
GAME_ID = f"{OURS}-vs-{THEIRS}"
GAME_UID = "43994252-2e4d-2b5c-9baa-4bf7aef5b5d6"
DIGEST = "9b0e173a79212271dea3f3b546591d7f93fe476ef7e7572aca34f8e88bccc142"
OTHER = "f" * 64


def rows(count: int = 6) -> list[dict[str, Any]]:
    return [
        settled_row(
            sub_game=n,
            ours=OURS,
            theirs=THEIRS,
            our_role=KitRole.POLICE if n % 2 else KitRole.THIEF,
            outcome=Outcome.SURVIVAL,
        )
        for n in range(1, count + 1)
    ]


def result(**changes: Any) -> dict[str, Any]:
    members: dict[str, Any] = {
        "game_id": GAME_ID,
        "game_uid": GAME_UID,
        "rows": rows(),
        "participants": [OURS, THEIRS],
        "github_links": {},
        "total_tokens": {},
        "timestamp": "2026-08-23T18:45:00Z",
        "consensus_sha256": DIGEST,
        "peer_consensus_sha256": DIGEST,
        **changes,
    }
    return dict(kit_result_document(**members))


# --- settlement and consensus -------------------------------------------------


def test_settlement_digest_mismatch_refuses_a_result() -> None:
    with pytest.raises(LocalDefectError, match="agreed on nothing"):
        result(peer_consensus_sha256=OTHER)


def test_report_before_consensus_refuses_a_result() -> None:
    with pytest.raises(LocalDefectError, match="waits for the peer's matching consensus"):
        result(peer_consensus_sha256=None)


def test_an_incomplete_series_refuses_a_result() -> None:
    with pytest.raises(LocalDefectError, match="covers 6 settled rows"):
        result(rows=rows(5))


# --- rows ---------------------------------------------------------------------


def test_a_row_conflict_is_refused_and_the_first_row_survives() -> None:
    """A sub-game settles once; a late duplicate must not change an agreed digest."""
    collected = SeriesRowCollector()
    first = rows(1)[0]
    collected.record(first)
    with pytest.raises(StaleMessageError, match="settles once"):
        collected.record(
            settled_row(
                sub_game=1,
                ours=OURS,
                theirs=THEIRS,
                our_role=KitRole.THIEF,
                outcome=Outcome.CAPTURE,
            )
        )
    assert collected.rows[1]["roles"] == first["roles"]


def test_a_row_outside_the_series_is_refused() -> None:
    collected = SeriesRowCollector()
    with pytest.raises(StaleMessageError):
        collected.record({**rows(1)[0], "sub_game_number": 9})
    assert collected.rows == {}


# --- official documents -------------------------------------------------------


def test_a_duplicate_document_is_refused_and_the_first_survives() -> None:
    collected = OfficialArtifactCollector()
    collected.record(LOG, 2, {"entries": ["original"]})
    with pytest.raises(StaleMessageError, match="settles once"):
        collected.record(LOG, 2, {"entries": ["replacement"]})
    assert collected.get(LOG, 2) == {"entries": ["original"]}


def test_an_unknown_document_family_is_refused() -> None:
    collected = OfficialArtifactCollector()
    with pytest.raises(StaleMessageError, match="not an official per-sub-game family"):
        collected.record("result", 1, {"a": 1})
    assert collected.documents == {}


def test_an_invalid_artifact_count_writes_nothing(tmp_path: Any) -> None:
    """Thirteen files is not a counted series, and half-writing one is worse."""
    collected = OfficialArtifactCollector()
    for number in range(1, 6):
        collected.record(CONFIG, number, {"config": {}})
        collected.record(LOG, number, {"entries": []})
    writer = CountedSeriesWriter(JsonArtifactStore(tmp_path), GAME_ID)
    with pytest.raises(StaleMessageError, match="missing"):
        writer.write(declaration={"game_id": GAME_ID}, collected=collected, result=result())
    assert list(tmp_path.iterdir()) == []


def test_a_result_that_was_never_agreed_writes_nothing(tmp_path: Any) -> None:
    collected = OfficialArtifactCollector()
    for number in range(1, 7):
        collected.record(CONFIG, number, {"config": {}})
        collected.record(LOG, number, {"entries": []})
    writer = CountedSeriesWriter(JsonArtifactStore(tmp_path), GAME_ID)
    with pytest.raises(LocalDefectError, match="waits for a mutual agreement"):
        writer.write(declaration={"game_id": GAME_ID}, collected=collected, result=None)
    assert list(tmp_path.iterdir()) == []


# --- run class ----------------------------------------------------------------


def test_a_rehearsal_refuses_to_report() -> None:
    with pytest.raises(LocalDefectError, match="never be counted or reported"):
        rehearsal().require_counted("the final report")


def test_a_rehearsal_refuses_every_counted_capability() -> None:
    for capability in ("the final report", "the result artifact", "counted evidence"):
        with pytest.raises(LocalDefectError):
            rehearsal().require_counted(capability)


def test_a_counted_run_refuses_development_evidence() -> None:
    with pytest.raises(LocalDefectError, match="belongs to a rehearsal"):
        counted().require_rehearsal("development evidence")


# --- the set itself -----------------------------------------------------------


def test_every_refusal_carries_a_typed_error_not_a_bare_exception() -> None:
    """A caller has to be able to tell a protocol refusal from a crash."""
    for call in (
        lambda: result(peer_consensus_sha256=OTHER),
        lambda: rehearsal().require_counted("x"),
        lambda: counted().require_rehearsal("x"),
    ):
        with pytest.raises(LocalDefectError):
            call()
    for stale in (
        lambda: OfficialArtifactCollector().record("nope", 1, {"a": 1}),
        lambda: SeriesRowCollector().record({"sub_game_number": 1}),
    ):
        with pytest.raises(StaleMessageError):
            stale()
