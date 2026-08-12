"""Two whole series that do not end well: a technical loss, and a tamper."""

import asyncio
import json
from pathlib import Path

import pytest
import test_two_agent_series as live
from r16_builders import GAME_ID

from mars777_police.app.protocol_errors import StaleMessageError
from mars777_police.app.protocol_values import FinalAuditVerdict
from mars777_police.domain.terminal import Outcome
from mars777_police.series_runtime import SeriesRuntime

TECHNICAL = (Outcome.CAPTURE, Outcome.TECHNICAL_LOSS) + (Outcome.CAPTURE,) * 4


def roots(tmp_path: Path) -> tuple[SeriesRuntime, SeriesRuntime]:
    return live.pair_for(tmp_path)


def test_a_series_containing_one_technical_loss_still_plays_exactly_six(tmp_path: Path) -> None:
    a, b = roots(tmp_path)
    asyncio.run(live.run_series(a, b, TECHNICAL))
    written: list[Path] = []
    for series in (a, b):
        assert [line.sub_game for line in series.lines] == [1, 2, 3, 4, 5, 6]
        loss = series.lines[1]
        assert (loss.outcome, loss.cop_score, loss.thief_score) == (Outcome.TECHNICAL_LOSS, 0, 0)
        assert series.sub_game == 6
        stored = series.persist_result()
        written.append(Path(stored.path))
        assert len(list(written[-1].parent.iterdir())) == 14
    document = json.loads(written[0].read_text("utf-8"))
    lines = document["sub_games"]
    assert [entry["outcome"] for entry in lines][1] == "technical_loss"
    assert (lines[1]["cop_score"], lines[1]["thief_score"]) == (0, 0)
    assert document["cumulative"] == {
        "cop_total": 100,
        "thief_total": 25,
        "series_outcome": "cop",
    }
    assert len(lines) == 6


def test_a_tampered_sub_game_blocks_the_result_but_keeps_the_evidence(tmp_path: Path) -> None:
    """The forensic artifacts stay; only the agreed result never comes into being."""
    a, b = roots(tmp_path)
    asyncio.run(live.run_series(a, b, (Outcome.CAPTURE,) * 6, tamper=True))
    audits = b.composition.series_audit
    assert audits.complete
    assert audits.verdict is FinalAuditVerdict.TAMPERED
    with pytest.raises(StaleMessageError):
        b.build_result()
    root = Path(b.store.root)  # type: ignore[attr-defined]
    assert not (root / f"result_{GAME_ID}.json").exists()
    assert len(list(root.iterdir())) == 13
    assert (root / f"log_{GAME_ID}_g01.json").exists()
    log = json.loads((root / f"log_{GAME_ID}_g01.json").read_text("utf-8"))
    assert log["audit"]["result"] == FinalAuditVerdict.TAMPERED.value
    assert log["audit"]["tampered_step"] == 1


def test_the_side_that_told_the_truth_still_audits_its_peer_as_verified(tmp_path: Path) -> None:
    a, b = roots(tmp_path)
    asyncio.run(live.run_series(a, b, (Outcome.CAPTURE,) * 6, tamper=True))
    assert a.composition.series_audit.verdict is FinalAuditVerdict.VERIFIED_OK
    assert b.composition.series_audit.verdict is FinalAuditVerdict.TAMPERED
