"""What a doctored config artifact cannot get past the read-back verifier.

Each case edits exactly one thing in a file production really wrote, and the
refusal comes from a production authority: the model's own validators, the two
digest recomputations, or the keyed proof. The interesting tamper is the one
that leaves the file internally consistent - a peer that recomputed a perfectly
valid proof over a digest the stored model does not have.
"""

import copy
import dataclasses
from pathlib import Path

import artifact_evidence_builders as evidence
import pytest
import r7_builders as r7
import series_freeze_builders as freeze
from pydantic import ValidationError

from mars777_police.app.peer_pregame_messages import ConfigLockEvidence
from mars777_police.app.protocol_errors import (
    AuthFailureError,
    ConfigMismatchError,
    MalformedMessageError,
)
from mars777_police.artifact_verification import verify_config_artifact
from mars777_police.protocol.scent_model import scent_model_sha256
from mars777_police.series_runtime import SeriesRuntime
from mars777_police.transport.codec_pregame import encode_lock
from mars777_police.transport.wire_artifacts import ConfigArtifactWire

OTHER = "b" * 64


def real(root: Path) -> tuple[SeriesRuntime, dict[str, object]]:
    """One real series and the artifact it actually wrote."""
    series = evidence.written(root)
    return series, evidence.read_artifact(root)


def refuse(series: SeriesRuntime, document: object) -> None:
    """Verify *document* with the provisioned authority - it must not pass."""
    verify_config_artifact(document, evidence.authority(series))  # type: ignore[arg-type]


def test_the_untouched_artifact_verifies(tmp_path: Path) -> None:
    series, document = real(tmp_path)
    verified = verify_config_artifact(document, evidence.authority(series))
    assert verified.config == r7.CONFIG


def test_a_fresh_model_b_artifact_verifies(tmp_path: Path) -> None:
    series = evidence.written(tmp_path, freeze.model_b())
    verified = verify_config_artifact(evidence.read_artifact(tmp_path), evidence.authority(series))
    assert verified.scent_model == freeze.model_b()


def test_one_changed_kernel_ring_with_the_stored_digest_is_refused(tmp_path: Path) -> None:
    """The digest is recomputed from the bytes, never trusted as written."""
    series, document = real(tmp_path)
    section = document["scent_model_evidence"]
    assert isinstance(section, dict)
    kernel = copy.deepcopy(section["model"])["kernel"]  # type: ignore[index]
    for row, col in ((0, 0), (0, 4), (4, 0), (4, 4)):
        kernel[row][col] = "0.03"
    changed = evidence.tampered(document, ("scent_model_evidence", "model", "kernel"), kernel)
    with pytest.raises(ConfigMismatchError, match="does not hash to the digest stored beside"):
        refuse(series, changed)


def test_an_untruthful_worked_example_is_refused_by_the_model_itself(tmp_path: Path) -> None:
    series, document = real(tmp_path)
    lying = [{"tau_before": "0.9", "delta": "0", "expected": "0.5"}]
    changed = evidence.tampered(document, ("scent_model_evidence", "model", "examples"), lying)
    with pytest.raises(MalformedMessageError, match=r"produces 0\.81"):
        refuse(series, changed)


def test_a_changed_stored_digest_with_the_same_model_is_refused(tmp_path: Path) -> None:
    series, document = real(tmp_path)
    changed = evidence.tampered(document, ("scent_model_evidence", "scent_model_sha256"), OTHER)
    with pytest.raises(ConfigMismatchError, match="does not hash to the digest stored beside"):
        refuse(series, changed)


def test_a_changed_context_digest_with_a_stale_proof_is_refused(tmp_path: Path) -> None:
    series, document = real(tmp_path)
    lock = copy.deepcopy(document["config_lock"])
    lock["context"]["scent_model_sha256"] = OTHER  # type: ignore[index]
    with pytest.raises(ConfigMismatchError, match="not the model the locked context names"):
        refuse(series, evidence.tampered(document, ("config_lock",), lock))


def test_a_recomputed_valid_proof_over_a_different_model_is_still_refused(tmp_path: Path) -> None:
    """The authenticated lie: the proof verifies, the stored model disagrees."""
    series, document = real(tmp_path)
    auth = evidence.authority(series)
    original = verify_config_artifact(document, auth)
    moved = dataclasses.replace(
        original.evidence.context, scent_model_sha256=scent_model_sha256(freeze.model_b())
    )
    relocked = encode_lock(ConfigLockEvidence(moved, auth.prove(moved))).model_dump(mode="json")
    assert auth.verify(moved, auth.prove(moved)), "the proof itself is genuinely valid"
    with pytest.raises(ConfigMismatchError, match="not the model the locked context names"):
        refuse(series, evidence.tampered(document, ("config_lock",), relocked))


def test_a_changed_config_core_with_the_stored_digest_is_refused(tmp_path: Path) -> None:
    series, document = real(tmp_path)
    world = copy.deepcopy(document["config"])["world"]  # type: ignore[index]
    world["hint_max_words"] = world["hint_max_words"] + 1
    core = evidence.tampered(document, ("config", "world"), world)
    with pytest.raises(ConfigMismatchError, match="not the core the locked context names"):
        refuse(series, core)


def test_an_artifact_without_scent_evidence_is_refused(tmp_path: Path) -> None:
    series, document = real(tmp_path)
    stripped = {key: value for key, value in document.items() if key != "scent_model_evidence"}
    with pytest.raises(MalformedMessageError, match="not a config artifact"):
        refuse(series, stripped)


def test_a_malformed_digest_is_refused_before_any_comparison(tmp_path: Path) -> None:
    series, document = real(tmp_path)
    changed = evidence.tampered(document, ("scent_model_evidence", "scent_model_sha256"), "nope")
    with pytest.raises(MalformedMessageError, match="not a config artifact"):
        refuse(series, changed)


def test_an_unknown_scent_evidence_member_follows_the_strict_policy(tmp_path: Path) -> None:
    series, document = real(tmp_path)
    section = copy.deepcopy(document["scent_model_evidence"])
    section["observed_by"] = "police"  # type: ignore[index]
    with pytest.raises(MalformedMessageError, match="not a config artifact"):
        refuse(series, evidence.tampered(document, ("scent_model_evidence",), section))
    with pytest.raises(ValidationError):
        ConfigArtifactWire.model_validate({**document, "extra": 1})


def test_a_proof_from_another_key_does_not_verify(tmp_path: Path) -> None:
    """Authorship needs the provisioned authority; the file never carries it."""
    series, document = real(tmp_path)
    lock = copy.deepcopy(document["config_lock"])
    lock["auth"]["value"] = "0" * 64  # type: ignore[index]
    with pytest.raises(AuthFailureError, match="does not verify over its context"):
        refuse(series, evidence.tampered(document, ("config_lock",), lock))
