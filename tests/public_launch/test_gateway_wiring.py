"""Assembling the group's front door, serving it, and releasing it again.

The gateway is routing and lifecycle and nothing else, so what is under test is
the wiring: it comes up from real operator input, it shows the operator only
what is safe to show, it reaches its backends, and it puts every session away -
including when the run ends by cancellation.
"""

import asyncio
from pathlib import Path

import pytest
from network_fixtures import POLICE_BACKEND
from operator_fixtures import free_port, operator_env, recorder

from mars777_police.app.kit_messages import KitRole
from mars777_police.transport.kit_backend_routes import KitBackendRoutes


def test_the_launcher_assembles_from_the_operator_environment(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from mars777_police.kit_gateway_main import build, parse_args

    operator_env(monkeypatch, tmp_path)
    launcher = build(
        parse_args(
            [
                "--police-endpoint",
                POLICE_BACKEND,
                "--thief-endpoint",
                "http://127.0.0.1:18932/mcp",
                "--ngrok",
                "/usr/bin/ngrok",
                "--evidence-root",
                str(tmp_path),
            ]
        )
    )

    assert launcher.group_id == "MaRs-777"
    assert len(launcher.backend_endpoints) == 2
    assert launcher.is_live is False
    assert sorted(launcher.gateway.routes) == sorted([KitRole.POLICE, KitRole.THIEF])


def test_serving_shows_the_operator_banner_and_releases_on_cancellation(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Ctrl-C during a wait is an ordinary ending, and it still tears down."""
    from network_fixtures import launcher, service, tracking_ingress

    from mars777_police.kit_gateway_main import serve

    ingress = tracking_ingress()
    held = launcher(service(ingress))

    async def run() -> None:
        task = asyncio.ensure_future(serve(held))
        for _ in range(500):
            if held.is_live:
                break
            await asyncio.sleep(0.01)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

    asyncio.run(run())

    assert "group_id" in capsys.readouterr().out
    assert ingress.closed is True
    assert held.is_live is False


def test_a_forwarder_reaches_its_backend_and_the_session_is_held() -> None:
    seen: list[str] = []
    port = free_port()
    server = recorder(port, seen)
    routes = KitBackendRoutes({KitRole.POLICE: f"http://127.0.0.1:{port}/mcp"}, 30.0)

    async def run() -> None:
        forward = routes.forwarders()[KitRole.POLICE]
        await forward("negotiate", {"message": {"a": 1}})
        await forward("negotiate", {"message": {"a": 2}})
        assert len(routes.clients) == 1
        await routes.close()

    try:
        asyncio.run(run())
    finally:
        server.should_exit = True

    assert seen == ["negotiate", "negotiate"]
    assert routes.clients == {}


def test_the_launcher_closes_the_backend_sessions_it_owns() -> None:
    """Routes are the launcher's to release; nothing else knows they exist."""
    from network_fixtures import launcher, service, tracking_ingress

    routes = KitBackendRoutes({KitRole.POLICE: POLICE_BACKEND}, 5.0)
    held = launcher(service(tracking_ingress()))
    held.routes = routes

    async def run() -> None:
        await held.open()
        await held.close()

    asyncio.run(run())

    assert held.routes is None
    assert routes.clients == {}
