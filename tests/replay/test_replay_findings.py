"""What the viewer says when the evidence is wrong, missing, or not a log."""

from pathlib import Path

import pytest
import replay_fixtures as fixtures

from mars777_police.sdk import AgentSdk, ReplayCheck, ReplayError

OTHER = "f" * 64


def opened(tmp_path: Path, edit: object = None) -> object:
    log, config = fixtures.played(tmp_path)
    if edit is not None:
        document = fixtures.document(log)
        edit(document)  # type: ignore[operator]
        fixtures.rewritten(log, document)
    return AgentSdk().open_replay(log, config)


def test_a_doctored_commitment_is_reported_as_tampered(tmp_path: Path) -> None:
    """REPLAY-002's other word, and it must not be softened."""

    def doctor(document: dict[str, object]) -> None:
        for entry in document["entries"]:  # type: ignore[union-attr]
            if entry["phase"] == "commit":
                entry["commit"] = OTHER
                return

    found = opened(tmp_path, doctor).summary()  # type: ignore[attr-defined]

    assert found.crypto is ReplayCheck.TAMPERED
    assert found.crypto.value == "TAMPERED"


def test_a_replay_continues_past_a_tampered_record(tmp_path: Path) -> None:
    """Forensic mode: every step is still shown, and the whole run is marked."""

    def doctor(document: dict[str, object]) -> None:
        for entry in document["entries"]:  # type: ignore[union-attr]
            if entry["phase"] == "commit":
                entry["commit"] = OTHER
                return

    replay = opened(tmp_path, doctor)

    assert len(replay.steps) == 2  # type: ignore[attr-defined]
    assert replay.summary().crypto is ReplayCheck.TAMPERED  # type: ignore[attr-defined]


def test_a_commitment_without_its_nonce_is_not_checkable(tmp_path: Path) -> None:
    """Missing evidence is never rendered as proof, and never as tampering."""

    def strip(document: dict[str, object]) -> None:
        document["audit"]["final_reveal"] = []  # type: ignore[index]

    found = opened(tmp_path, strip).summary()  # type: ignore[attr-defined]

    assert found.crypto is ReplayCheck.NOT_CHECKABLE


def test_a_moved_cell_is_caught_by_the_semantic_authority(tmp_path: Path) -> None:
    def doctor(document: dict[str, object]) -> None:
        for entry in document["entries"]:  # type: ignore[union-attr]
            if entry["phase"] == "commit":
                entry["state"]["self_pos"] = [6, 6]
                return

    found = opened(tmp_path, doctor).summary()  # type: ignore[attr-defined]

    assert found.semantic_verdict != "CONSISTENT"
    assert found.outcome_agrees is False


def test_development_evidence_is_refused_with_the_reason(tmp_path: Path) -> None:
    """A friendly contribution holds no board by contract; saying so is the point."""
    log, config = fixtures.played(tmp_path)
    fixtures.rewritten(log, {"evidence_class": "DEVELOPMENT_EVIDENCE", "role": "police"})

    with pytest.raises(ReplayError, match="development evidence"):
        AgentSdk().open_replay(log, config)


def test_a_missing_file_is_a_sentence_not_a_traceback(tmp_path: Path) -> None:
    _, config = fixtures.played(tmp_path)

    with pytest.raises(ReplayError, match="cannot read"):
        AgentSdk().open_replay(tmp_path / "absent.json", config)


def test_bytes_that_are_not_json_are_refused(tmp_path: Path) -> None:
    log, config = fixtures.played(tmp_path)
    log.write_text("{not json", encoding="utf-8")

    with pytest.raises(ReplayError, match="not valid JSON"):
        AgentSdk().open_replay(log, config)


def test_a_log_with_no_committed_step_cannot_be_walked(tmp_path: Path) -> None:
    def empty(document: dict[str, object]) -> None:
        document["entries"] = []

    replay = opened(tmp_path, empty)

    with pytest.raises(ReplayError, match="no committed step"):
        replay.first()  # type: ignore[attr-defined]
