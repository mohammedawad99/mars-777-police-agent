"""The one facade operation that answers about a file rather than a network.

It is the operation an auditor actually wants: hand it a config artifact a real
series wrote and it says what the bytes prove, or refuses them. The verification
authority is the operator's provisioned key, read from the environment exactly as
it is at boot, because an artifact never carries the material needed to check its
own authorship.
"""

from pathlib import Path

import artifact_evidence_builders as evidence
import pytest
import r7_builders as r7
from executable_process import environment

from mars777_police.app.protocol_errors import AuthFailureError, MalformedMessageError
from mars777_police.compose_verify import verify_stored_config
from mars777_police.infra.settings import SettingsError
from mars777_police.sdk import AgentSdk


def operator_env(monkeypatch: pytest.MonkeyPatch, root: Path) -> None:
    for name, value in environment(root=root).items():
        monkeypatch.setenv(name, value)


def written(tmp_path: Path) -> dict[str, object]:
    """A config artifact a real locked series left on disk."""
    evidence.written(tmp_path)
    return evidence.read_artifact(tmp_path)


def test_the_facade_verifies_an_artifact_a_real_series_wrote(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    operator_env(monkeypatch, tmp_path)

    verified = AgentSdk().verify_config_artifact(written(tmp_path))

    assert verified.config == r7.CONFIG


def test_a_document_that_is_not_a_config_artifact_is_refused(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    operator_env(monkeypatch, tmp_path)

    with pytest.raises(MalformedMessageError):
        verify_stored_config({"not": "a config artifact"})


def test_a_reader_without_the_provisioned_key_is_told_so(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A different key proves nothing about authorship, and says so."""
    document = written(tmp_path)
    operator_env(monkeypatch, tmp_path)
    monkeypatch.setenv("MARS777_AUTH_SECRET", "a-different-provisioned-secret")

    with pytest.raises(AuthFailureError):
        verify_stored_config(document)


def test_verification_still_needs_an_operator_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The settings boundary refuses first; no artifact is even decoded."""
    for name in ("MARS777_ROLE", "MARS777_KEY_ID", "MARS777_AUTH_SECRET"):
        monkeypatch.delenv(name, raising=False)

    with pytest.raises(SettingsError):
        verify_stored_config({"anything": True})
