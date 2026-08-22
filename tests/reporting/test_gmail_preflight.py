"""The pre-match readiness check: safe to run, and never aimed at the lecturer.

Its job is to fail *early*. Appendix E rule 35 scores a missing report 0 for
both groups, so an expired refresh token must be discovered before a counted
series starts, not after a result exists.

Every test here runs offline. The one network call the command can make is an
OAuth refresh, and it is only reached when a real credential is configured.
"""

import stat
from pathlib import Path

import pytest

from mars777_police import gmail_preflight
from mars777_police.app.report_values import REPORTS_ADDRESS
from mars777_police.infra.gmail_credentials import SEND_SCOPE, TOKEN_PATH


def test_a_missing_environment_variable_is_not_ready_and_contacts_nobody() -> None:
    found = gmail_preflight.checks(env={})

    assert found[0][0] == TOKEN_PATH
    assert found[0][1] is False
    assert len(found) == 1


def test_a_missing_token_file_stops_before_reading_anything(tmp_path: Path) -> None:
    found = gmail_preflight.checks(env={TOKEN_PATH: str(tmp_path / "absent.json")})
    names = [one[0] for one in found]

    assert "token file exists" in names
    assert not any(one[1] for one in found if one[0] == "token file exists")
    assert "live token refresh" not in names


def test_a_world_readable_token_is_reported_as_not_private(tmp_path: Path) -> None:
    """A tournament credential anyone on the box can read is not ready.

    Asked of the POSIX branch explicitly, so this holds on every platform: a
    Windows runner cannot produce `0644` through `chmod`, but the rule being
    tested - "any group or other bit means not private" - is the same one.
    """
    token = tmp_path / "token.json"
    token.write_text("{}", encoding="utf-8")
    token.chmod(0o644)

    _, ok, reason = gmail_preflight._permissions(token, system="posix")

    assert ok is False
    assert "mode 0" in reason


def test_the_posix_branch_reports_the_real_mode_it_read(tmp_path: Path) -> None:
    """The decision follows the mode the filesystem actually gave us."""
    import stat as stat_module

    token = tmp_path / "token.json"
    token.write_text("{}", encoding="utf-8")
    token.chmod(0o600)
    mode = stat_module.S_IMODE(token.stat().st_mode)

    _, ok, reason = gmail_preflight._permissions(token, system="posix")

    assert ok is ((mode & 0o077) == 0)
    assert f"{mode:04o}" in reason


def test_windows_reports_the_check_as_inapplicable_rather_than_failing(
    tmp_path: Path,
) -> None:
    """`os.chmod` on Windows toggles read-only and nothing else.

    NTFS then reports `0666` for a file an ACL may protect perfectly well, so a
    POSIX bit test there would answer `GMAIL_PREFLIGHT_READY = NO` forever and
    block counted play over a healthy credential.
    """
    token = tmp_path / "token.json"
    token.write_text("{}", encoding="utf-8")

    _, ok, reason = gmail_preflight._permissions(token, system="nt")

    assert ok is True
    assert "not checkable on Windows" in reason


def test_a_private_but_invalid_token_fails_on_schema_not_on_the_network(
    tmp_path: Path,
) -> None:
    token = tmp_path / "token.json"
    token.write_text("{}", encoding="utf-8")
    token.chmod(0o600)

    found = gmail_preflight.checks(env={TOKEN_PATH: str(token)})
    names = [one[0] for one in found]

    assert next(one for one in found if one[0] == "credential schema")[1] is False
    assert "live token refresh" not in names


def test_the_command_says_no_and_exits_two_when_unconfigured(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.delenv(TOKEN_PATH, raising=False)

    status = gmail_preflight.main([])

    assert status == 2
    assert gmail_preflight.NOT_READY in capsys.readouterr().out


def test_the_preflight_never_names_the_lecturer_as_a_destination() -> None:
    """It compares the constant; it must never send anywhere."""
    import inspect

    body = inspect.getsource(gmail_preflight)

    assert "users/me/messages/send" not in body
    assert "message_bytes" not in body
    assert REPORTS_ADDRESS in body


def test_the_preflight_prints_no_secret(tmp_path: Path) -> None:
    token = tmp_path / "token.json"
    token.write_text("{}", encoding="utf-8")
    token.chmod(0o600)

    reasons = " ".join(one[2] for one in gmail_preflight.checks(env={TOKEN_PATH: str(token)}))

    for secret in ("refresh_token=", "client_secret=", "Bearer ", "ya29."):
        assert secret not in reasons


def test_the_scope_it_checks_is_send_only() -> None:
    assert SEND_SCOPE == "https://www.googleapis.com/auth/gmail.send"
    assert "gmail.modify" not in SEND_SCOPE
    assert "mail.google.com" not in SEND_SCOPE


def test_permissions_helper_accepts_an_owner_only_file(tmp_path: Path) -> None:
    token = tmp_path / "t.json"
    token.write_text("{}", encoding="utf-8")
    token.chmod(0o600)

    _, ok, _ = gmail_preflight._permissions(token, system="posix")

    assert ok is ((stat.S_IMODE(token.stat().st_mode) & 0o077) == 0)
