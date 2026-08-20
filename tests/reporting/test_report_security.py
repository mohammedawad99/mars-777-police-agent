"""What the reporting path must never do, checked rather than promised.

Appendix E rule 39 forbids pushing secrets to the repository at all and rule 40
requires the credential files in `.gitignore`; rule 30 restricts the Gmail scope
to send-only. Beside those, a report carries text this process did not author -
a `game_id` a peer proposed - so header injection is a real path, not a
theoretical one.
"""

import json
from pathlib import Path

import pytest
import report_fixtures as fix

from mars777_police.app.report_message import message_bytes, safe_header
from mars777_police.app.report_values import ReportError
from mars777_police.infra.gmail_credentials import (
    SEND_SCOPE,
    TOKEN_PATH,
    GmailCredentialError,
    credentials_path,
    load_credentials,
)

REPO = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize("hostile", ["a\r\nBcc: attacker@example.test", "a\nX: y", "a\x00b"])
def test_a_header_component_carrying_a_control_character_is_refused(hostile: str) -> None:
    with pytest.raises(ReportError, match="control character"):
        safe_header(hostile, "test")


def test_a_hostile_game_id_cannot_smuggle_a_header_into_the_message() -> None:
    with pytest.raises(ReportError, match="control character"):
        message_bytes(fix.report(game_id="g\r\nBcc: attacker@example.test"))


def test_an_empty_header_component_is_refused_rather_than_defaulted() -> None:
    with pytest.raises(ReportError, match="non-empty"):
        safe_header("   ", "test")


def test_a_result_document_containing_the_separator_is_refused() -> None:
    with pytest.raises(ReportError, match="separator"):
        message_bytes(fix.report(attachment=b'{"x": "----=_MaRs-777-report"}'))


def test_the_credential_refuses_to_render_itself_in_any_form() -> None:
    from mars777_police.infra.gmail_credentials import GmailCredentials

    held = GmailCredentials("client-id", "very-secret", "refresh-secret")

    rendered = f"{held!r} {held} {held.__dict__ if hasattr(held, '__dict__') else ''}"
    assert "very-secret" not in rendered
    assert "refresh-secret" not in rendered


def test_a_token_file_granting_more_than_send_is_refused(tmp_path: Path) -> None:
    target = tmp_path / "token.json"
    target.write_text(
        json.dumps(
            {
                "client_id": "a",
                "client_secret": "b",
                "refresh_token": "c",
                "scopes": ["https://mail.google.com/"],
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(GmailCredentialError, match="send-only"):
        load_credentials(target)


def test_a_send_only_token_file_is_accepted(tmp_path: Path) -> None:
    target = tmp_path / "token.json"
    target.write_text(
        json.dumps(
            {"client_id": "a", "client_secret": "b", "refresh_token": "c", "scopes": [SEND_SCOPE]}
        ),
        encoding="utf-8",
    )

    assert load_credentials(target).client_id == "a"


def test_an_absent_credential_variable_names_the_variable_and_no_value() -> None:
    with pytest.raises(GmailCredentialError, match=TOKEN_PATH):
        credentials_path({})


@pytest.mark.parametrize("missing", ["client_id", "client_secret", "refresh_token"])
def test_an_incomplete_credential_file_is_refused_by_field_name(
    tmp_path: Path, missing: str
) -> None:
    document = {"client_id": "a", "client_secret": "b", "refresh_token": "c"}
    del document[missing]
    target = tmp_path / "token.json"
    target.write_text(json.dumps(document), encoding="utf-8")

    with pytest.raises(GmailCredentialError, match=missing):
        load_credentials(target)


def test_the_credential_files_the_source_names_are_git_ignored() -> None:
    ignored = (REPO / ".gitignore").read_text(encoding="utf-8")

    for name in ("credentials.json", "token.json"):
        assert name in ignored


def test_the_repository_contains_no_credential_file() -> None:
    for name in ("credentials.json", "token.json"):
        assert not (REPO / name).exists()
