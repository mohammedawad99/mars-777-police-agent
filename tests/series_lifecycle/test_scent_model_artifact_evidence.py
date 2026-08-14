"""What the config artifact proves once the live session that wrote it is gone.

The file has to carry the whole agreed model - twenty-five weights, three
Appendix-F values and both worked numbers - because a reader that had to
reconstruct it from a name would be trusting the name. Beside it sits the model's
own identity and the lock context that authenticated it, so one file joins:

    full model -> scent_model_sha256 -> authenticated ConfigLockContext

while the 35-member core keeps its own separate identity in the same context.

Every assertion below reads bytes back from disk and verifies them through the
production `verify_config_artifact`, never against the objects that wrote them.
"""

import json
from pathlib import Path

import artifact_evidence_builders as evidence
import r7_builders as r7
import series_freeze_builders as freeze
from r16_builders import config

from mars777_police.app.config_artifact_values import ConfigArtifactContent
from mars777_police.artifact_verification import verify_config_artifact
from mars777_police.domain.scent_model_default import FIGURE_4_WEIGHTS, default_scent_model
from mars777_police.protocol.canonical import canonical_json_bytes
from mars777_police.protocol.config_lock import config_sha256
from mars777_police.protocol.scent_model import scent_model_core, scent_model_sha256
from mars777_police.series_runtime import SeriesRuntime

CANONICAL_BYTES = 344
CONFIG_VECTOR = "b9bdf822ecc143a4a283bbf3ae6cd3bcdba9da80b7c470a73dce404f9ce44bd8"


def verified(root: Path, series: SeriesRuntime) -> ConfigArtifactContent:
    """The artifact on disk, verified with the provisioned authority."""
    return verify_config_artifact(evidence.read_artifact(root), evidence.authority(series))


def test_the_artifact_has_exactly_the_three_sections(tmp_path: Path) -> None:
    series = evidence.written(tmp_path)
    document = evidence.read_artifact(tmp_path)
    assert set(document) == {"config", "config_lock", "scent_model_evidence"}
    assert verified(tmp_path, series).config == r7.CONFIG


def test_the_whole_agreed_model_is_persisted(tmp_path: Path) -> None:
    """Not a name and not a digest: every member a peer had to interpret."""
    evidence.written(tmp_path)
    model = evidence.read_artifact(tmp_path)["scent_model_evidence"]
    assert isinstance(model, dict)
    written = model["model"]
    assert isinstance(written, dict)
    assert written["model_id"] == "BOUNDED_SATURATING_RADIAL_V1"
    assert [len(row) for row in written["kernel"]] == [5] * 5  # type: ignore[union-attr]
    assert written["kernel"] == [list(row) for row in FIGURE_4_WEIGHTS]
    assert len(written["examples"]) == 2  # type: ignore[arg-type]


def test_every_number_survives_as_canonical_decimal_text(tmp_path: Path) -> None:
    """No JSON float ever touches the model: the bytes carry the spellings."""
    evidence.written(tmp_path)
    raw = (tmp_path / "police" / evidence.NAME).read_text(encoding="utf-8")
    written = json.loads(raw)["scent_model_evidence"]["model"]
    assert (written["decay"], written["center_intensity"]) == ("0.10", "0.9")
    assert written["kernel"][2][2] == "0.90"
    assert [one["expected"] for one in written["examples"]] == ["0.81", "0.9"]
    assert '"decay":"0.10"' in raw, "text on disk, not a float"


def test_the_read_back_model_reproduces_both_golden_vectors(tmp_path: Path) -> None:
    series = evidence.written(tmp_path)
    model = verified(tmp_path, series).scent_model
    assert model == default_scent_model()
    assert len(canonical_json_bytes(scent_model_core(model))) == CANONICAL_BYTES
    assert scent_model_sha256(model) == freeze.GOLDEN


def test_the_stored_digest_is_the_one_the_stored_model_hashes_to(tmp_path: Path) -> None:
    series = evidence.written(tmp_path)
    document = evidence.read_artifact(tmp_path)
    stored = document["scent_model_evidence"]
    assert isinstance(stored, dict)
    assert stored["scent_model_sha256"] == freeze.GOLDEN.value
    model = verified(tmp_path, series).scent_model
    assert scent_model_sha256(model).value == stored["scent_model_sha256"]


def test_the_stored_digest_is_the_one_the_locked_context_names(tmp_path: Path) -> None:
    series = evidence.written(tmp_path)
    proved = verified(tmp_path, series)
    context = proved.evidence.context
    assert context.scent_model_sha256 == freeze.GOLDEN
    assert context.scent_model_sha256 == scent_model_sha256(proved.scent_model)


def test_the_config_core_keeps_its_own_independent_identity(tmp_path: Path) -> None:
    """Two identities, one context: the digests are never merged."""
    series = evidence.written(tmp_path)
    proved = verified(tmp_path, series)
    context = proved.evidence.context
    assert config_sha256(proved.config) == context.config_sha256
    assert context.config_sha256 != context.scent_model_sha256
    assert config_sha256(r7.CONFIG) == context.config_sha256


def test_the_thirty_five_member_core_is_stored_alone_in_its_section(tmp_path: Path) -> None:
    evidence.written(tmp_path)
    core = evidence.read_artifact(tmp_path)["config"]
    assert isinstance(core, dict)
    assert not {"scent_model_sha256", "model_id", "kernel", "config_auth"} & set(core)
    assert config_sha256(config()).value == CONFIG_VECTOR, "the frozen vector is untouched"


def test_the_persisted_proof_verifies_over_the_persisted_context(tmp_path: Path) -> None:
    series = evidence.written(tmp_path)
    proved = verified(tmp_path, series)
    auth = evidence.authority(series)
    assert auth.verify(proved.evidence.context, proved.evidence.auth)


def test_a_fresh_series_persists_the_model_it_actually_agreed(tmp_path: Path) -> None:
    """Model B, not the project default: nothing is reconstructed on write."""
    other = freeze.model_b()
    series = evidence.written(tmp_path, other)
    proved = verified(tmp_path, series)
    assert proved.scent_model == other != default_scent_model()
    stored = evidence.read_artifact(tmp_path)["scent_model_evidence"]
    assert isinstance(stored, dict)
    assert stored["scent_model_sha256"] == scent_model_sha256(other).value
    assert proved.evidence.context.scent_model_sha256 == scent_model_sha256(other)
