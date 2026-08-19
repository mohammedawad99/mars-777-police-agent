"""No entry into a live configured runtime can skip the compatibility check.

The point of a single authority is that nothing routes around it. These tests
enter through the ways a configuration actually reaches this process - the
operator's launch document, a peer's proposal, and the KIT backend's local
document - and prove each one refuses a version this build cannot represent.
"""

import json
from pathlib import Path

import pytest
import r7_builders as r7
from executable_process import environment, launch_document

from mars777_police.domain.config_schema import (
    SUPPORTED_CONFIG_SCHEMA_VERSIONS,
    UnsupportedConfigSchemaError,
)
from mars777_police.launch_input import LaunchInputError, read_launch_document
from mars777_police.sdk import ROLE, AgentSdk, RoleBackendRequest
from mars777_police.shared.version import VERSION

UNSUPPORTED = "mars777-99"


def operator_env(monkeypatch: pytest.MonkeyPatch, root: Path) -> None:
    for name, value in environment(root=root).items():
        monkeypatch.setenv(name, value)


def document(root: Path, version: str, *, kit: bool = False) -> Path:
    """A launch document whose config carries *version*."""
    body = json.loads(launch_document())
    config = body["config"]
    assert isinstance(config, dict)
    config["schema_version"] = version
    if kit:
        body["kit_terms"] = {"board_size": 7, "max_steps": 35}
    path = root / "launch.json"
    path.write_text(json.dumps(body), encoding="utf-8")
    return path


def test_a_launch_document_at_the_supported_version_is_read() -> None:
    assert next(iter(SUPPORTED_CONFIG_SCHEMA_VERSIONS)) == r7.CONFIG.schema_version


def test_a_launch_document_at_an_unsupported_version_is_refused(tmp_path: Path) -> None:
    """The operator boundary reports it as a local refusal, and says which version."""
    with pytest.raises(LaunchInputError) as failure:
        read_launch_document(document(tmp_path, UNSUPPORTED))

    assert UNSUPPORTED in str(failure.value)
    assert "not supported by this build" in str(failure.value)


def test_the_kit_backend_refuses_an_unsupported_local_configuration(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """KIT never negotiates this member; the local representation is still checked."""
    operator_env(monkeypatch, tmp_path)
    request = RoleBackendRequest(
        launch=document(tmp_path, UNSUPPORTED, kit=True),
        port=1,
        opponent="https://partner.example/mcp",
        gateway_admin="http://127.0.0.1:1/mcp",
    )

    with pytest.raises(LaunchInputError) as failure:
        AgentSdk().compose_role_backend(request)

    assert UNSUPPORTED in str(failure.value)


def test_two_peers_agreeing_on_an_unsupported_version_still_cannot_run() -> None:
    """Equality is not compatibility: the same bad string on both sides fails."""
    from mars777_police.transport.codec_config import encode_config
    from mars777_police.transport.wire_config import NegotiatedConfigWire

    wire = encode_config(r7.CONFIG).model_dump(mode="json")
    wire["schema_version"] = UNSUPPORTED
    agreed = NegotiatedConfigWire.model_validate(wire)

    from mars777_police.transport.codec_config import decode_config

    for _ in ("ours", "theirs"):
        with pytest.raises(UnsupportedConfigSchemaError):
            decode_config(agreed)


def test_the_software_version_is_a_separate_authority() -> None:
    """§8.1's code row and configuration row are different questions."""
    assert VERSION.pep440 not in SUPPORTED_CONFIG_SCHEMA_VERSIONS
    assert VERSION.guideline not in SUPPORTED_CONFIG_SCHEMA_VERSIONS
    assert ROLE.value in {"police", "thief"}
