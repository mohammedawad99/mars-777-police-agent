"""When a config artifact may be written at all, and what it never contains.

The file is evidence of a lock, so the writer refuses to produce one before a
lock this side actually verified - including for the sub-game whose bilateral
model switch the series refused, which must leave no file claiming otherwise.

The atomic store keeps its existing guarantee underneath: one complete file or
none, a byte-identical rewrite is the same evidence, and a contradicting rewrite
is refused rather than allowed to change history.
"""

import dataclasses
from pathlib import Path

import artifact_evidence_builders as evidence
import pytest
import r7_builders as r7
import series_freeze_builders as freeze
from r16_builders import GAME_ID

from mars777_police.app.protocol_errors import ConfigMismatchError, LocalDefectError
from mars777_police.app.protocol_values import Sha256Digest
from mars777_police.artifact_documents import config_document
from mars777_police.artifact_verification import verify_config_artifact
from mars777_police.domain.scent_model_default import default_scent_model
from mars777_police.transport.codec_artifacts import read_config_artifact
from mars777_police.transport.wire_artifacts import ConfigArtifactWire

SECRETS = ("out-of-band-provisioned-secret", "PRIVATE KEY", "authtoken", "oauth", "ssh-rsa")


def test_a_sub_game_with_no_verified_lock_writes_no_artifact(tmp_path: Path) -> None:
    """The file reports a lock, so a round that never locked has nothing to say."""
    a, b = freeze.pair(tmp_path)
    freeze.negotiate(a, b, 1, default_scent_model())
    with pytest.raises(LocalDefectError, match="waits for a lock this side verified"):
        a.lock_config(r7.CONFIG)
    assert not list(tmp_path.glob("*/config_*.json"))


def test_a_refused_mid_series_switch_writes_no_artifact_claiming_it(tmp_path: Path) -> None:
    """Both peers moved to B, the series refused, and no g02 file says otherwise."""
    a, b = freeze.pair(tmp_path)
    freeze.lock(a, b, 1, default_scent_model())
    a.lock_config(r7.CONFIG)
    freeze.negotiate(a, b, 2, freeze.model_b())
    with pytest.raises(ConfigMismatchError, match="already locked its scent model"):
        a.composition.pregame.accept_lock(b.composition.pregame.prepare_lock())
    with pytest.raises(LocalDefectError, match="waits for a lock this side verified"):
        a.lock_config(r7.CONFIG)
    assert [path.name for path in sorted(tmp_path.glob("police/config_*.json"))] == [evidence.NAME]
    written = verify_config_artifact(evidence.read_artifact(tmp_path), evidence.authority(a))
    assert written.scent_model == default_scent_model(), "g01's evidence is untouched"


def test_the_refused_sub_game_leaves_no_partial_file(tmp_path: Path) -> None:
    a, b = freeze.pair(tmp_path)
    freeze.negotiate(a, b, 1, default_scent_model())
    with pytest.raises(LocalDefectError):
        a.lock_config(r7.CONFIG)
    assert not list(tmp_path.glob("*/*.partial"))


def test_rewriting_the_same_evidence_is_the_same_artifact(tmp_path: Path) -> None:
    """A retry writes the evidence already on disk, so it is not a contradiction."""
    series = evidence.written(tmp_path)
    before = (tmp_path / "police" / evidence.NAME).read_bytes()
    again = series.lock_config(r7.CONFIG)
    assert (tmp_path / "police" / evidence.NAME).read_bytes() == before
    assert again.digest.value and not list(tmp_path.glob("*/*.partial"))


def test_a_different_agreed_model_cannot_overwrite_a_written_artifact(tmp_path: Path) -> None:
    """History is never edited: the store refuses a second, different evidence."""
    series = evidence.written(tmp_path)
    before = (tmp_path / "police" / evidence.NAME).read_bytes()
    evidence.written(tmp_path / "second", freeze.model_b())
    with pytest.raises(LocalDefectError, match="already exists with different content"):
        series.store.store(evidence.NAME, evidence.read_artifact(tmp_path / "second"))
    assert (tmp_path / "police" / evidence.NAME).read_bytes() == before


def test_a_document_may_not_report_a_model_the_verified_lock_does_not_name(
    tmp_path: Path,
) -> None:
    """A locally swapped model after the lock is a defect, not a new agreement."""
    a, b = freeze.pair(tmp_path)
    freeze.lock(a, b, 1, default_scent_model())
    pregame = a.composition.pregame
    pregame.lock = dataclasses.replace(pregame.lock, scent_model=freeze.model_b())
    with pytest.raises(LocalDefectError, match="not the one the verified lock names"):
        config_document(r7.CONFIG, pregame)


def test_a_document_may_not_report_a_core_the_verified_lock_does_not_name(
    tmp_path: Path,
) -> None:
    a, b = freeze.pair(tmp_path)
    freeze.lock(a, b, 1, default_scent_model())
    other = dataclasses.replace(
        r7.CONFIG, world=dataclasses.replace(r7.CONFIG.world, hint_max_words=9)
    )
    with pytest.raises(LocalDefectError, match="not the locked core"):
        config_document(other, a.composition.pregame)


def test_the_artifact_carries_a_key_label_and_no_key_material(tmp_path: Path) -> None:
    evidence.written(tmp_path)
    raw = (tmp_path / "police" / f"config_{GAME_ID}_g01.json").read_text(encoding="utf-8")
    assert "mars777-k1" in raw, "the label a reader needs to pick the right key"
    for secret in SECRETS:
        assert secret not in raw


def test_the_parser_alone_accepts_only_the_three_named_sections(tmp_path: Path) -> None:
    evidence.written(tmp_path)
    wire = read_config_artifact(evidence.read_artifact(tmp_path))
    assert set(ConfigArtifactWire.model_fields) == {
        "config",
        "config_lock",
        "scent_model_evidence",
    }
    assert Sha256Digest(wire.scent_model_evidence.scent_model_sha256) == freeze.GOLDEN
