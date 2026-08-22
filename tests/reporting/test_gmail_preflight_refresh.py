"""The live-refresh half of the pre-match check, exercised entirely offline.

Every network call here is faked. The point of these tests is that an expired,
revoked or over-scoped credential fails the **preflight**, before a counted
series starts - never during one, and never by contacting Google from CI.
"""

from pathlib import Path

import pytest

from mars777_police import gmail_preflight
from mars777_police.app.report_values import REPORTS_ADDRESS
from mars777_police.infra.gmail_credentials import SEND_SCOPE, TOKEN_PATH


def _credential(tmp_path: Path) -> Path:
    """A schema-valid credential whose values are obvious placeholders."""
    import json

    token = tmp_path / "token.json"
    token.write_text(
        json.dumps(
            {
                "client_id": "placeholder-client",
                "client_secret": "placeholder-secret",
                "refresh_token": "placeholder-refresh",
                "scopes": [SEND_SCOPE],
            }
        ),
        encoding="utf-8",
    )
    token.chmod(0o600)
    return token


def test_a_healthy_credential_reports_ready_without_touching_the_real_endpoint(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The success path, with the refresh faked: no network, no Google, no mail."""
    monkeypatch.setattr(
        gmail_preflight,
        "refresh",
        lambda credentials: ("live token refresh", True, "expires_in=3599s"),
    )

    found = gmail_preflight.checks(env={TOKEN_PATH: str(_credential(tmp_path))})

    assert all(ok for _, ok, _ in found)
    assert [one[0] for one in found][-1] == "live token refresh"
    assert any(one[0] == "recipient constant" and one[2] == REPORTS_ADDRESS for one in found)
    assert any(one[0] == "rate-limit config loads" and one[1] for one in found)


def test_the_command_says_yes_and_exits_zero_when_everything_is_ready(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv(TOKEN_PATH, str(_credential(tmp_path)))
    monkeypatch.setattr(
        gmail_preflight, "refresh", lambda credentials: ("live token refresh", True, "ok")
    )

    status = gmail_preflight.main([])

    assert status == 0
    assert gmail_preflight.READY in capsys.readouterr().out


def test_an_http_error_from_the_token_endpoint_is_not_ready(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An expired or revoked refresh token must fail the preflight, not the match."""
    import urllib.error

    from mars777_police.infra.gmail_credentials import load_credentials

    def angry(*args: object, **kwargs: object) -> object:
        raise urllib.error.HTTPError("https://oauth2.googleapis.com/token", 400, "Bad", {}, None)  # type: ignore[arg-type]

    monkeypatch.setattr(gmail_preflight.urllib.request, "urlopen", angry)
    _, ok, reason = gmail_preflight.refresh(load_credentials(_credential(tmp_path)))

    assert ok is False
    assert "HTTP 400" in reason


def test_an_unreachable_token_endpoint_is_not_ready(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from mars777_police.infra.gmail_credentials import load_credentials

    def offline(*args: object, **kwargs: object) -> object:
        raise OSError("no route to host")

    monkeypatch.setattr(gmail_preflight.urllib.request, "urlopen", offline)
    _, ok, reason = gmail_preflight.refresh(load_credentials(_credential(tmp_path)))

    assert ok is False
    assert "unreachable" in reason


def test_a_refresh_granting_a_wider_scope_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Least privilege is checked at the door, not assumed from the file."""
    import contextlib
    import io
    import json

    from mars777_police.infra.gmail_credentials import load_credentials

    @contextlib.contextmanager
    def wide(*args: object, **kwargs: object):  # type: ignore[no-untyped-def]
        yield io.BytesIO(
            json.dumps({"scope": "https://mail.google.com/", "expires_in": 3599}).encode()
        )

    monkeypatch.setattr(gmail_preflight.urllib.request, "urlopen", wide)
    _, ok, reason = gmail_preflight.refresh(load_credentials(_credential(tmp_path)))

    assert ok is False
    assert "send scope" in reason


def test_the_preflight_is_runnable_as_a_module(tmp_path: Path) -> None:
    """`python -m ..._preflight` is the documented pre-match command.

    Run with no credential configured, so the child exits 2 having contacted
    nothing at all.
    """
    import os
    import subprocess
    import sys

    root = Path(__file__).resolve().parents[2]
    environment = {key: value for key, value in os.environ.items() if key != TOKEN_PATH}

    finished = subprocess.run(
        [sys.executable, "-m", "mars777_police.gmail_preflight"],
        capture_output=True,
        text=True,
        check=False,
        cwd=root,
        env={**environment, "PYTHONPATH": str(root / "src")},
    )

    assert finished.returncode == 2
    assert gmail_preflight.NOT_READY in finished.stdout


def test_a_successful_refresh_reports_the_expiry_without_the_token(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The happy path of the real refresh function, with the socket faked."""
    import contextlib
    import io
    import json

    from mars777_police.infra.gmail_credentials import load_credentials

    @contextlib.contextmanager
    def granted(*args: object, **kwargs: object):  # type: ignore[no-untyped-def]
        yield io.BytesIO(
            json.dumps(
                {"access_token": "must-not-appear", "scope": SEND_SCOPE, "expires_in": 3599}
            ).encode()
        )

    monkeypatch.setattr(gmail_preflight.urllib.request, "urlopen", granted)
    _, ok, reason = gmail_preflight.refresh(load_credentials(_credential(tmp_path)))

    assert ok is True
    assert "expires_in=3599s" in reason
    assert "must-not-appear" not in reason


def test_an_unreadable_rate_limit_configuration_is_not_ready(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A gate that cannot load is a gate that cannot protect the provider."""

    def broken() -> None:
        raise RuntimeError("rate limits unreadable")

    monkeypatch.setattr(gmail_preflight, "load_rate_limits", broken)
    monkeypatch.setattr(
        gmail_preflight, "refresh", lambda credentials: ("live token refresh", True, "ok")
    )

    found = gmail_preflight.checks(env={TOKEN_PATH: str(_credential(tmp_path))})
    gate = next(one for one in found if one[0] == "rate-limit config loads")

    assert gate[1] is False
    assert gate[2] == "RuntimeError"
    assert not all(ok for _, ok, _ in found)
