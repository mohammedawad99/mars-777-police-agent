"""The facade forwards; it never decides.

Each test replaces the composition function the operation delegates to and
proves two things: the call reached it with exactly what the caller asked for,
and the facade returned what it answered. A facade that computed anything of its
own would fail these by returning something the double never produced.
"""

import asyncio
from pathlib import Path

import pytest

from mars777_police.sdk import (
    AgentSdk,
    ExternalMode,
    KitRole,
    PublicGatewayRequest,
    RoleBackendRequest,
    SoftwareVersionError,
    StrictSeriesRequest,
)


def test_building_the_facade_verifies_this_installation() -> None:
    """A stale wheel shadowing the source tree is refused at construction."""
    with pytest.raises(SoftwareVersionError):
        AgentSdk(lookup=lambda _: "9.9")


def test_a_strict_series_forwards_the_launch_document_and_the_wire(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from mars777_police import compose_series

    seen: dict[str, object] = {}

    async def played(request: StrictSeriesRequest) -> Path:
        seen["request"] = request
        return Path("/artifacts")

    monkeypatch.setattr(compose_series, "run_strict_series", played)
    request = StrictSeriesRequest(launch=Path("doc.json"), external_mode=ExternalMode.KIT_CORE_V1)

    assert asyncio.run(AgentSdk().run_strict_series(request)) == Path("/artifacts")
    assert seen["request"] is request


def test_composing_a_role_backend_forwards_the_whole_request(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from mars777_police import compose_backend

    seen: dict[str, object] = {}
    monkeypatch.setattr(
        compose_backend, "compose_role_backend", lambda request: seen.setdefault("r", request)
    )
    request = RoleBackendRequest(
        launch=Path("doc.json"),
        port=1,
        opponent="https://x.example/mcp",
        gateway_admin="http://127.0.0.1:1/mcp",
        first_role=KitRole.THIEF,
    )

    assert AgentSdk().compose_role_backend(request) is request
    assert seen["r"] is request


def test_writing_a_contribution_forwards_the_backend_and_the_root(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from mars777_police import compose_backend

    monkeypatch.setattr(
        compose_backend, "write_contribution", lambda backend, root: f"{backend}:{root}"
    )

    assert AgentSdk().write_contribution("BACKEND", Path("root")) == "BACKEND:root"  # type: ignore[arg-type]


def test_composing_the_public_gateway_forwards_the_whole_request(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from mars777_police import compose_gateway

    monkeypatch.setattr(compose_gateway, "compose_public_gateway", lambda request: request)
    request = PublicGatewayRequest(
        police_endpoint="http://127.0.0.1:1/mcp",
        thief_endpoint="http://127.0.0.1:2/mcp",
        first_role=KitRole.POLICE,
        ngrok=Path("/usr/bin/ngrok"),
        evidence_root=Path("runtime/friendly"),
    )

    assert AgentSdk().compose_public_gateway(request) is request


def test_verifying_a_stored_config_forwards_the_document(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from mars777_police import compose_verify

    monkeypatch.setattr(compose_verify, "verify_stored_config", lambda document: document)
    document = {"kind": "config"}

    assert AgentSdk().verify_config_artifact(document) is document  # type: ignore[comparison-overlap]
