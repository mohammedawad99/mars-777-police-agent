"""Assembling one role backend, serving its private port, and what it writes.

A backend reads its role from this repository and its sub-games from the frozen
schedule; it invents neither. These pin what it refuses when the launch document
cannot support a friendly, what it reports when its private port is already
taken, and the development name its contribution is written under.
"""

import asyncio
import socket
from pathlib import Path

import pytest
from executable_process import launch_document
from operator_fixtures import (
    admin_server,
    empty_chain,
    free_port,
    kit_launch_document,
    operator_env,
)

from mars777_police.app.kit_messages import KitRole


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
    held.chains[number] = empty_chain()

    written = persist(held, tmp_path)

    assert Path(written).name.startswith("friendly_")
    assert Path(written).exists()
