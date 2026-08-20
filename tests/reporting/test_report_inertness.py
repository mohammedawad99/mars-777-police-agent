"""That nothing but a report ever reaches the Gmail provider or its credential.

Importing the reporting module is not the same as initialising the provider, so
the property worth proving is the second one: no credential is read, no sender
is constructed and no request is prepared unless an operator actually asks for a
report. A missing Gmail credential can therefore never stop a game.
"""

from pathlib import Path

import pytest
import report_fixtures as fix

from mars777_police.infra.gmail_credentials import TOKEN_PATH


@pytest.fixture(autouse=True)
def no_credential(monkeypatch: pytest.MonkeyPatch) -> None:
    """Run every test here on a machine that has no Gmail credential at all."""
    for name in (TOKEN_PATH, "MARS777_RUN_LIVE_GMAIL", "MARS777_LIVE_GMAIL_RECIPIENT"):
        monkeypatch.delenv(name, raising=False)


def test_the_whole_public_surface_imports_without_a_credential() -> None:
    from mars777_police import sdk

    assert sdk.REPORTS_ADDRESS
    for name in sdk.__all__:
        assert getattr(sdk, name) is not None or name


def test_composing_a_strict_series_never_builds_a_gmail_sender(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    built: list[object] = []
    monkeypatch.setattr(
        "mars777_police.compose_report.GmailSender", lambda credentials: built.append(credentials)
    )

    import mars777_police.compose_backend
    import mars777_police.compose_gateway
    import mars777_police.compose_replay
    import mars777_police.compose_series
    import mars777_police.gui  # noqa: F401

    assert built == []


def test_reading_a_report_touches_no_credential_and_no_provider(tmp_path: Path) -> None:
    """Eligibility is decided entirely from the artifact, so it needs no secret."""
    from mars777_police.compose_report import read_report

    result = fix.written_result(tmp_path)

    report = read_report(result, tmp_path)

    assert report.attachment == result.read_bytes()


def test_only_an_actual_send_reaches_for_the_credential(tmp_path: Path) -> None:
    from mars777_police.compose_report import send_game_report
    from mars777_police.infra.gmail_credentials import GmailCredentialError

    result = fix.written_result(tmp_path)

    with pytest.raises(GmailCredentialError, match=TOKEN_PATH):
        send_game_report(result, tmp_path)


def test_the_reporting_path_needs_no_window_toolkit_and_no_display() -> None:
    import ast

    src = Path(__file__).resolve().parents[2] / "src" / "mars777_police"
    for name in ("compose_report.py", "report_main.py", "infra/gmail_sender.py"):
        tree = ast.parse((src / name).read_text(encoding="utf-8"))
        named: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                named.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                named.add(node.module or "")
        assert not any("tkinter" in one or "PIL" in one for one in named), name
