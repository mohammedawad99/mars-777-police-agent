"""What the official log says about scent once it is read back off the disk.

A whole real series is played between two production agents over real FastMCP,
the fourteen official files are written by the real store, and every assertion
opens the bytes that landed and joins them against the semantic history the live
protocol left behind - never against the object that produced them.

The readback is semantic, not textual: the persisted deposits are handed to the
same Part-1A parser the audit disclosure already uses, and what comes out has to
be the `ScentEmission` the turn carried - same cells, same order, same `Decimal`
spellings, no float anywhere on the path."""

import asyncio
import json
from collections.abc import Iterator
from pathlib import Path

import pytest
import r7_builders as r7
import test_two_agent_series as live
from r16_builders import GAME_ID

from mars777_police.app.audit_scent import scent_rows
from mars777_police.app.protocol_values import FinalAuditVerdict
from mars777_police.app.scent_json import deposits_value
from mars777_police.domain.terminal import Outcome

REVEAL = "reveal"
OWN_ROLE, PEER_ROLE = "police", "thief"


@pytest.fixture(scope="module")
def played(tmp_path_factory: pytest.TempPathFactory) -> Iterator[tuple[Path, object]]:
    """One real completed series, played once, read back many times."""
    root = tmp_path_factory.mktemp("scent-series")
    a, b = live.pair_for(root)
    asyncio.run(live.run_series(a, b, (Outcome.CAPTURE,) * 5 + (Outcome.SURVIVAL,)))
    for series in (a, b):
        series.persist_result()
    yield root / "police", a


def read(root: Path, name: str) -> dict[str, object]:
    """Read one official artifact back as JSON, exactly as a reader would."""
    document = json.loads((root / name).read_text(encoding="utf-8"))
    assert isinstance(document, dict)
    return document


def reveal_events(log: dict[str, object]) -> list[dict[str, object]]:
    entries = log["entries"]
    assert isinstance(entries, list)
    return [one for one in entries if one["phase"] == REVEAL]


def parsed(deposits: object, step: int) -> object:
    """The persisted deposits back through the one existing scent parser."""
    document = {"sub_game": 1, "scent": [{"step": step, "emission": deposits}]}
    (row,) = scent_rows(document)
    return row.emission


def test_every_reveal_in_every_log_carries_its_scent_evidence(played: tuple) -> None:
    root, _ = played
    for sub_game in range(1, 7):
        events = reveal_events(read(root, f"log_{GAME_ID}_g0{sub_game}.json"))
        assert events, f"sub-game {sub_game} played turns"
        for event in events:
            deposits = event["scent_emission"]
            assert isinstance(deposits, list) and deposits, "a counted reveal deposited something"


def test_the_persisted_scent_is_the_scent_the_live_turn_carried(played: tuple) -> None:
    """Log ↔ live history: bytes off the disk against the values the turn retained.

    The last sub-game's owners are still bound when the series ends, so its two
    retained histories are the ones this file has to agree with."""
    root, series = played
    context = series.composition.runtime_context
    evidence, audit = context.current_evidence(), context.current_audit()
    assert evidence.context.sub_game == 6
    log = read(root, f"log_{GAME_ID}_g06.json")
    events = reveal_events(log)
    ours = [one["scent_emission"] for one in events if one["role"] == OWN_ROLE]
    theirs = [one["scent_emission"] for one in events if one["role"] == PEER_ROLE]
    assert ours == [deposits_value(row.emission) for row in evidence.scent]
    assert theirs == [deposits_value(row.emission) for row in audit.expected_scent]
    assert ours and theirs, "both halves of the turn were written"


def test_the_persisted_deposits_parse_back_to_the_same_semantic_emission(played: tuple) -> None:
    root, _ = played
    log = read(root, f"log_{GAME_ID}_g01.json")
    for event in reveal_events(log):
        deposits = event["scent_emission"]
        assert isinstance(deposits, list)
        emission = parsed(deposits, int(str(event["step"])))
        assert deposits_value(emission) == deposits, "rendering and parsing are inverses"


def test_every_persisted_intensity_is_canonical_text_and_never_a_number(played: tuple) -> None:
    root, _ = played
    for sub_game in range(1, 7):
        for event in reveal_events(read(root, f"log_{GAME_ID}_g0{sub_game}.json")):
            deposits = event["scent_emission"]
            assert isinstance(deposits, list)
            for deposit in deposits:
                assert isinstance(deposit["intensity"], str)
                assert isinstance(deposit["cell"], list) and len(deposit["cell"]) == 2


def test_the_persisted_bytes_disclose_no_position_of_any_emitter(played: tuple) -> None:
    root, _ = played
    text = (root / f"log_{GAME_ID}_g01.json").read_text(encoding="utf-8")
    for forbidden in ("source_position", "own_position", "opponent", "true_position"):
        assert forbidden not in text


def test_the_commit_and_ack_events_persist_no_scent(played: tuple) -> None:
    root, _ = played
    log = read(root, f"log_{GAME_ID}_g01.json")
    entries = log["entries"]
    assert isinstance(entries, list)
    for entry in entries:
        if entry["phase"] != REVEAL:
            assert "scent_emission" not in entry


def test_the_four_families_still_write_exactly_fourteen_files_and_no_sidecar(
    played: tuple,
) -> None:
    root, _ = played
    written = sorted(one.name for one in root.iterdir())
    assert len(written) == 14 and not list(root.glob("*.partial"))
    assert len([one for one in written if one.startswith("log_")]) == 6
    assert len([one for one in written if one.startswith("config_")]) == 6
    for name in written:
        assert name.startswith(("declaration_", "config_", "log_", "result_"))
        assert "scent" not in name


def test_the_existing_audit_block_of_every_log_is_untouched(played: tuple) -> None:
    root, _ = played
    for sub_game in range(1, 7):
        audit = read(root, f"log_{GAME_ID}_g0{sub_game}.json")["audit"]
        assert isinstance(audit, dict)
        assert set(audit) == {"final_reveal", "result", "tampered_step", "semantic"}
        assert audit["result"] == FinalAuditVerdict.VERIFIED_OK.value
        assert audit["tampered_step"] is None
        assert r7.GAME_UID
