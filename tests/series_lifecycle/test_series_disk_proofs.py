"""What the fourteen official files say once they are read back from disk.

Every assertion opens the bytes that were written, decodes them through the
existing semantic boundaries, and joins them against each other - never against
the in-memory object that produced them.
"""

import asyncio
import json
from collections.abc import Iterator
from pathlib import Path

import pytest
import r7_builders as r7
import test_two_agent_series as live
from r16_builders import GAME_ID

from mars777_police.app.audit_disclosure import identity, turns
from mars777_police.app.protocol_values import FinalAuditVerdict
from mars777_police.app.result_core_runtime import participants_of
from mars777_police.app.series_record import own_team
from mars777_police.domain.terminal import Outcome
from mars777_police.protocol.config_lock import config_sha256
from mars777_police.transport.codec_config import decode_config
from mars777_police.transport.codec_declaration import decode_declaration
from mars777_police.transport.wire_config import NegotiatedConfigWire
from mars777_police.transport.wire_declaration import DeclarationWire

VERIFIED = FinalAuditVerdict.VERIFIED_OK.value
SECRETS = {
    "shared auth secret": "out-of-band-provisioned-secret",
    "auth env value": "MARS777_AUTH_SECRET",
    "oauth material": "oauth",
    "ngrok token": "authtoken",
    "private key": "PRIVATE KEY",
    "ssh material": "ssh-rsa",
    "environ dump": "MARS777_BIND_HOST",
}


@pytest.fixture(scope="module")
def played(tmp_path_factory: pytest.TempPathFactory) -> Iterator[Path]:
    """One real completed series, played once, read back many times."""
    root = tmp_path_factory.mktemp("series")
    a, b = live.pair_for(root)
    asyncio.run(live.run_series(a, b, (Outcome.CAPTURE,) * 5 + (Outcome.SURVIVAL,)))
    for series in (a, b):
        series.persist_result()
    yield root / "police"


def disclosure_view(log: dict[str, object]) -> dict[str, object]:
    """The log's commit events, back in the shape the frozen disclosure parser reads."""
    entries = log["entries"]
    assert isinstance(entries, list)
    commits = [
        {key: value for key, value in entry.items() if key not in ("phase", "verified")}
        for entry in entries
        if entry["phase"] == "commit"
    ]
    return {**log, "entries": commits}


def read(root: Path, name: str) -> dict[str, object]:
    """Read one official artifact back as JSON, exactly as a reader would."""
    document = json.loads((root / name).read_text(encoding="utf-8"))
    assert isinstance(document, dict)
    return document


def test_the_completed_series_wrote_exactly_the_fourteen_official_files(played: Path) -> None:
    assert len(sorted(played.iterdir())) == 14 and not list(played.glob("*.partial"))


def test_the_declaration_decodes_through_the_existing_semantic_boundary(played: Path) -> None:
    document = read(played, f"declaration_{GAME_ID}.json")
    declaration = decode_declaration(DeclarationWire.model_validate(document))
    assert declaration.game_id == GAME_ID
    assert participants_of(declaration).group_a


def test_each_config_decodes_and_matches_its_log_digest(played: Path) -> None:
    """INV-02 and INV-03, proven from bytes: gNN joins gNN, digest joins digest."""
    for sub_game in range(1, 7):
        artifact = read(played, f"config_{GAME_ID}_g0{sub_game}.json")
        wire = NegotiatedConfigWire.model_validate(artifact["config"])
        config = decode_config(wire)
        log = read(played, f"log_{GAME_ID}_g0{sub_game}.json")
        game_id, game_uid, logged_sub_game, digest = identity(log)
        assert (game_id, logged_sub_game) == (GAME_ID, sub_game)
        assert game_uid == r7.GAME_UID
        assert digest == config_sha256(config).value
        assert turns(disclosure_view(log))


def test_every_log_reports_a_verified_audit_and_its_own_nonces(played: Path) -> None:
    for sub_game in range(1, 7):
        audit = read(played, f"log_{GAME_ID}_g0{sub_game}.json")["audit"]
        assert isinstance(audit, dict)
        assert (audit["result"], audit["tampered_step"]) == (VERIFIED, None)
        steps = {entry["step"] for entry in audit["final_reveal"]}  # type: ignore[union-attr]
        assert steps == {1, 2}


def test_one_real_turn_is_written_commit_then_ack_then_reveal(played: Path) -> None:
    """The ack event comes from the real runtime acknowledgement, not the renderer."""
    log = read(played, f"log_{GAME_ID}_g01.json")
    entries = log["entries"]
    assert isinstance(entries, list)
    phases = [entry["phase"] for entry in entries]
    assert phases[:3] == ["commit", "ack", "reveal"]
    commit, ack = entries[0], entries[1]
    assert ack["ack_of_step"] == commit["step"]
    assert ack["ack_commit"] == commit["commit"]
    assert ack["by_role"] != commit["role"]
    assert {entry["phase"] for entry in entries} == {"commit", "ack", "reveal"}


def test_the_result_joins_the_declaration_and_the_recorded_lines(played: Path) -> None:
    result = read(played, f"result_{GAME_ID}.json")
    declaration = decode_declaration(
        DeclarationWire.model_validate(read(played, f"declaration_{GAME_ID}.json"))
    )
    assert result["game_id"] == GAME_ID and result["game_uid"] == r7.GAME_UID
    assert result["declaration_ref"] == f"declaration_{GAME_ID}.json"
    sub_games = result["sub_games"]
    assert isinstance(sub_games, list)
    assert [entry["sub_game"] for entry in sub_games] == [1, 2, 3, 4, 5, 6]
    assert [entry["outcome"] for entry in sub_games][-1] == "survival"
    assert result["cumulative"] == {"cop_total": 105, "thief_total": 35, "series_outcome": "cop"}
    for slot in ("group_a", "group_b"):
        declared = own_team(declaration, str(participants_of(declaration).__getattribute__(slot)))
        commits = {entry["github_commit"][slot] for entry in sub_games}
        assert commits == {declared.github_commit.value}
        totals = sum(int(entry["tokens"][slot]) for entry in sub_games)
        assert totals == result["total_tokens"][slot]  # type: ignore[index]
    assert result["mutual_agreement"] is True
    assert len(str(result["result_sha256"])) == 64
    assert "result_sha256" not in json.dumps(result["sub_games"])
    assert result["reported_by"]


def test_no_official_artifact_carries_a_secret_or_a_local_path(played: Path) -> None:
    for path in sorted(played.iterdir()):
        text = path.read_text(encoding="utf-8")
        for category, needle in SECRETS.items():
            assert needle not in text, f"{path.name} leaked {category}"
        assert str(played) not in text
        assert "/home/" not in text and "C:\\" not in text
