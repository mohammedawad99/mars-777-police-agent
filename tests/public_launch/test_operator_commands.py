"""That each command can actually be started, and what it says when it finishes.

A command nobody can run classifies nothing, so each entrypoint is proved
runnable as a module. A backend that finished its rows then has one thing to
tell the operator: where the contribution went.
"""

from pathlib import Path

import pytest
from network_fixtures import POLICE_BACKEND
from operator_fixtures import empty_chain, free_port, kit_launch_document, operator_env


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
        boot.backend.chains[number] = empty_chain()
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
