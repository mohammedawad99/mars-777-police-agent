"""Assembling each command from real operator input, and releasing it again.

These are the paths a real launch takes: read the environment, read the launch
document, build the graph, serve, forward, report settlement, release. They are
exercised against local recorders rather than a provider, because what is under
test is the wiring - the provider already has its own live proof.
"""

import asyncio
import json
import socket
import threading
import time
from pathlib import Path

import pytest
import uvicorn
from executable_process import environment, launch_document
from fastmcp import FastMCP
from network_fixtures import POLICE_BACKEND

from mars777_police.app.kit_messages import KitRole
from mars777_police.transport.kit_backend_routes import KitBackendRoutes


def free_port() -> int:
    held = socket.socket()
    held.bind(("127.0.0.1", 0))
    port = int(held.getsockname()[1])
    held.close()
    return port


def recorder(port: int, seen: list[str]) -> uvicorn.Server:
    """A private local stand-in for one role backend."""
    app: FastMCP = FastMCP("recorder")

    @app.tool
    async def negotiate(message: dict[str, object]) -> dict[str, bool]:
        seen.append("negotiate")
        return {"ok": True}

    config = uvicorn.Config(
        app.http_app(path="/mcp"), host="127.0.0.1", port=port, log_level="error"
    )
    server = uvicorn.Server(config)
    threading.Thread(target=server.run, daemon=True).start()
    while not server.started:
        time.sleep(0.05)
    return server


def operator_env(monkeypatch: pytest.MonkeyPatch, root: Path) -> None:
    for name, value in environment(root=root).items():
        monkeypatch.setenv(name, value)


def kit_launch_document(root: Path) -> Path:
    """The counted launch document plus the flat terms a KIT pairing agreed."""
    document = json.loads(launch_document())
    document["kit_terms"] = {"board_size": 7, "max_steps": 35}
    path = root / "launch.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    return path


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


def test_the_backend_assembles_from_a_launch_document_that_carries_the_terms(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from mars777_police.kit_backend_main import build, parse_args

    operator_env(monkeypatch, tmp_path)
    boot = build(
        parse_args(
            [
                "--launch",
                str(kit_launch_document(tmp_path)),
                "--port",
                str(free_port()),
                "--opponent",
                "https://partner.example/mcp",
                "--gateway-admin",
                "http://127.0.0.1:1/mcp",
            ]
        )
    )

    assert boot.backend.context.our_group == "MaRs-777"
    assert boot.backend.ours in ((1, 3, 5), (2, 4, 6))
    assert boot.client.url == "https://partner.example/mcp"


def test_a_launch_document_without_the_agreed_terms_is_refused(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from mars777_police.kit_backend_main import build, parse_args
    from mars777_police.launch_input import LaunchInputError

    operator_env(monkeypatch, tmp_path)
    path = tmp_path / "counted.json"
    path.write_text(launch_document(), encoding="utf-8")

    with pytest.raises(LaunchInputError):
        build(
            parse_args(
                [
                    "--launch",
                    str(path),
                    "--port",
                    "1",
                    "--opponent",
                    "https://x.example/mcp",
                    "--gateway-admin",
                    "http://127.0.0.1:1/mcp",
                ]
            )
        )


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


def admin_server(port: int, seen: list[int]) -> uvicorn.Server:
    """A private stand-in for the gateway's loopback settlement surface."""
    app: FastMCP = FastMCP("admin")

    @app.tool
    async def sub_game_settled(sub_game: int) -> dict[str, bool]:
        seen.append(sub_game)
        return {"ok": True}

    config = uvicorn.Config(
        app.http_app(path="/mcp"), host="127.0.0.1", port=port, log_level="error"
    )
    server = uvicorn.Server(config)
    threading.Thread(target=server.run, daemon=True).start()
    while not server.started:
        time.sleep(0.05)
    return server


def test_a_backend_boot_serves_reports_settlement_and_releases_everything() -> None:
    from kit_backend_builders import backend

    from mars777_police.domain.terminal import Outcome
    from mars777_police.kit_backend_boot import KitBackendBoot, backend_client

    settled: list[int] = []
    admin_port, private_port = free_port(), free_port()
    server = admin_server(admin_port, settled)
    template = backend(KitRole.POLICE)

    class Reporting(type(template)):  # type: ignore[misc]
        async def run(self) -> dict[int, Outcome]:
            """Report one settlement, exactly as a played sub-game would."""
            await self.settled(4)
            return {4: Outcome.SURVIVAL}

    held = Reporting(
        **{
            field.name: getattr(template, field.name)
            for field in __import__("dataclasses").fields(template)
        }
    )
    boot = KitBackendBoot(
        held,
        held.context,
        backend_client(f"http://127.0.0.1:{admin_port}/mcp", 5.0),
        f"http://127.0.0.1:{admin_port}/mcp",
        private_port,
    )

    try:
        outcomes = asyncio.run(boot.run())
    finally:
        server.should_exit = True

    assert outcomes == {4: Outcome.SURVIVAL}
    assert settled == [4]
    assert boot.served is not None


def test_a_private_port_already_in_use_fails_before_anything_serves() -> None:
    from kit_backend_builders import backend

    from mars777_police.kit_backend_boot import KitBackendBoot, backend_client

    taken = socket.socket()
    taken.bind(("127.0.0.1", 0))
    taken.listen(1)
    port = int(taken.getsockname()[1])
    held = backend(KitRole.POLICE)
    boot = KitBackendBoot(
        held,
        held.context,
        backend_client("https://x.example/mcp", 5.0),
        "http://127.0.0.1:1/mcp",
        port,
    )

    try:
        with pytest.raises(OSError):
            asyncio.run(boot._serve())
    finally:
        taken.close()


def test_a_contribution_is_written_under_a_development_name(tmp_path: Path) -> None:
    from kit_backend_builders import backend
    from test_kit_backend_flow import _pairing

    from mars777_police.domain.terminal import Outcome
    from mars777_police.kit_backend_main import persist

    held = backend(KitRole.POLICE)
    number = held.ours[0]
    held.friendly.record_pairing(_pairing())
    held.outcomes[number] = Outcome.SURVIVAL
    held.verified[number] = True
    held.witnessed.steps[number] = 34
    held.chains[number] = _empty_chain()

    written = persist(held, tmp_path)

    assert Path(written).name.startswith("friendly_")
    assert Path(written).exists()


def _empty_chain() -> object:
    from mars777_police.app.commitment_codecs import CommitmentCodec
    from mars777_police.app.kit_records import KitRecordChain
    from mars777_police.protocol.secure_nonce import SecretsNonceSource

    return KitRecordChain(CommitmentCodec.KIT_CORE_COMMITMENT_V1, SecretsNonceSource())


def test_each_command_reports_a_clean_stop_as_status_zero(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Ctrl-C is an ordinary ending for both, and neither invents a failure."""
    from mars777_police import kit_backend_main, kit_gateway_main

    operator_env(monkeypatch, tmp_path)

    def interrupted(coroutine: object) -> None:
        getattr(coroutine, "close", lambda: None)()
        raise KeyboardInterrupt

    monkeypatch.setattr(kit_gateway_main.asyncio, "run", interrupted)
    monkeypatch.setattr(kit_backend_main.asyncio, "run", interrupted)

    assert (
        kit_gateway_main.main(
            [
                "--police-endpoint",
                POLICE_BACKEND,
                "--thief-endpoint",
                POLICE_BACKEND,
                "--ngrok",
                "/usr/bin/ngrok",
            ]
        )
        == 0
    )
    assert (
        kit_backend_main.main(
            [
                "--launch",
                str(kit_launch_document(tmp_path)),
                "--port",
                str(free_port()),
                "--opponent",
                "https://partner.example/mcp",
                "--gateway-admin",
                "http://127.0.0.1:1/mcp",
            ]
        )
        == 0
    )


def test_a_public_route_that_never_comes_up_is_status_four(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """An ingress that will not open is an operator condition, not a peer fault."""
    from mars777_police import kit_gateway_main
    from mars777_police.app.public_ingress import PublicIngressError

    operator_env(monkeypatch, tmp_path)

    def refuse(coroutine: object) -> None:
        getattr(coroutine, "close", lambda: None)()
        raise PublicIngressError("the agent never registered an endpoint")

    monkeypatch.setattr(kit_gateway_main.asyncio, "run", refuse)

    assert (
        kit_gateway_main.main(
            [
                "--police-endpoint",
                POLICE_BACKEND,
                "--thief-endpoint",
                POLICE_BACKEND,
                "--ngrok",
                "/usr/bin/ngrok",
            ]
        )
        == 4
    )


def test_a_finished_backend_writes_its_contribution_and_says_where(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    from test_kit_backend_flow import _pairing

    from mars777_police import kit_backend_main
    from mars777_police.domain.terminal import Outcome

    operator_env(monkeypatch, tmp_path)
    played: dict[str, object] = {}

    def finished(coroutine: object) -> dict[int, Outcome]:
        getattr(coroutine, "close", lambda: None)()
        return {}

    monkeypatch.setattr(kit_backend_main.asyncio, "run", finished)
    original = kit_backend_main.build

    def build(arguments: object) -> object:
        boot = original(arguments)
        boot.backend.friendly.record_pairing(_pairing())
        number = boot.backend.ours[0]
        boot.backend.outcomes[number] = Outcome.SURVIVAL
        boot.backend.verified[number] = True
        boot.backend.witnessed.steps[number] = 34
        boot.backend.chains[number] = _empty_chain()
        played["boot"] = boot
        return boot

    monkeypatch.setattr(kit_backend_main, "build", build)

    status = kit_backend_main.main(
        [
            "--launch",
            str(kit_launch_document(tmp_path)),
            "--port",
            str(free_port()),
            "--opponent",
            "https://partner.example/mcp",
            "--gateway-admin",
            "http://127.0.0.1:1/mcp",
            "--evidence-root",
            str(tmp_path / "evidence"),
        ]
    )

    assert status == 0
    assert "contribution written to" in capsys.readouterr().out


def test_a_launcher_that_stops_normally_is_status_zero(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from mars777_police import kit_gateway_main

    operator_env(monkeypatch, tmp_path)

    def finished(coroutine: object) -> None:
        getattr(coroutine, "close", lambda: None)()

    monkeypatch.setattr(kit_gateway_main.asyncio, "run", finished)

    assert (
        kit_gateway_main.main(
            [
                "--police-endpoint",
                POLICE_BACKEND,
                "--thief-endpoint",
                POLICE_BACKEND,
                "--ngrok",
                "/usr/bin/ngrok",
            ]
        )
        == 0
    )


@pytest.mark.parametrize(
    "module", ["mars777_police.kit_gateway_main", "mars777_police.kit_backend_main"]
)
def test_each_command_is_runnable_as_a_module(module: str, tmp_path: Path) -> None:
    """`python -m …` really is the entry point, and it refuses an empty environment."""
    import os
    import subprocess
    import sys

    clean = {k: v for k, v in os.environ.items() if not k.startswith("MARS777_")}
    argv = (
        [
            "--police-endpoint",
            POLICE_BACKEND,
            "--thief-endpoint",
            POLICE_BACKEND,
            "--ngrok",
            "/usr/bin/ngrok",
        ]
        if module.endswith("gateway_main")
        else [
            "--launch",
            str(tmp_path / "absent.json"),
            "--port",
            "1",
            "--opponent",
            "https://x.example/mcp",
            "--gateway-admin",
            "http://127.0.0.1:1/mcp",
        ]
    )

    finished = subprocess.run(
        [sys.executable, "-m", module, *argv], env=clean, capture_output=True, text=True
    )

    assert finished.returncode == 2
    assert "cannot start" in finished.stderr


def test_the_admin_client_refuses_to_report_before_its_session_is_open() -> None:
    """A settlement that never left is worse than one that failed loudly."""
    from mars777_police.transport.kit_admin_client import KitAdminClient

    with pytest.raises(RuntimeError):
        asyncio.run(KitAdminClient("http://127.0.0.1:1/mcp").settled(1))


def test_closing_an_admin_client_that_never_opened_is_safe() -> None:
    from mars777_police.transport.kit_admin_client import KitAdminClient

    asyncio.run(KitAdminClient("http://127.0.0.1:1/mcp").__aexit__(None, None, None))
