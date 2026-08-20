"""What each command's exit status classifies.

Status is a classification, not a summary: a clean stop is zero whichever way the
run ended, and a public route that never came up is four rather than a generic
failure. An operator who cannot tell those apart cannot act on either.
"""

from pathlib import Path

import pytest
from network_fixtures import POLICE_BACKEND
from operator_fixtures import free_port, kit_launch_document, operator_env


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
