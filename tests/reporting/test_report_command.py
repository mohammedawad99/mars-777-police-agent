"""The command an operator runs, and every status it can leave behind.

A normal credential or provider failure must read as a sentence with an exit
code, never as a traceback: an operator whose token expired needs to know which
variable to set, not where the exception was raised.
"""

from pathlib import Path

import pytest
import report_fixtures as fix

from mars777_police import report_main
from mars777_police.app.gatekeeper_retry import ProviderStatusError
from mars777_police.infra.gmail_credentials import TOKEN_PATH


def token_file(tmp_path: Path) -> Path:
    target = tmp_path / "token.json"
    target.write_text(
        '{"client_id": "a", "client_secret": "b", "refresh_token": "c"}', encoding="utf-8"
    )
    return target


def wired(monkeypatch: pytest.MonkeyPatch, provider: fix.FakeGmail, tmp_path: Path) -> None:
    """Point the composition at a fake provider and a throwaway credential."""
    monkeypatch.setenv(TOKEN_PATH, str(token_file(tmp_path)))
    monkeypatch.setattr("mars777_police.compose_report.GmailSender", lambda credentials: provider)


def test_a_missing_credential_names_the_variable_and_exits_two(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.delenv(TOKEN_PATH, raising=False)
    result = fix.written_result(tmp_path)
    capsys.readouterr()

    status = report_main.main(["--result", str(result)])

    assert status == 2
    assert TOKEN_PATH in capsys.readouterr().err


def test_an_unagreed_result_is_refused_before_any_provider_is_reached(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    provider = fix.FakeGmail()
    wired(monkeypatch, provider, tmp_path)
    result = fix.written_result(tmp_path, mutual_agreement=False)
    capsys.readouterr()

    status = report_main.main(["--result", str(result)])

    assert status == 2
    assert "mutual agreement" in capsys.readouterr().err
    assert provider.sent == []


def test_a_missing_result_file_is_a_sentence_rather_than_a_traceback(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    wired(monkeypatch, fix.FakeGmail(), tmp_path)
    capsys.readouterr()

    status = report_main.main(["--result", str(tmp_path / "absent.json")])

    assert status == 2
    assert "cannot report" in capsys.readouterr().err


def test_an_accepted_report_prints_the_recipient_and_exits_zero(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    provider = fix.FakeGmail(["17f0abcd"])
    wired(monkeypatch, provider, tmp_path)
    result = fix.written_result(tmp_path)
    capsys.readouterr()

    status = report_main.main(["--result", str(result)])
    printed = capsys.readouterr().out

    assert status == 0
    assert "rmisegal+uoh26finalgame@gmail.com" in printed
    assert "17f0abcd" in printed
    assert len(provider.sent) == 1


def test_a_refused_report_is_status_three_and_says_reporting_is_incomplete(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    wired(monkeypatch, fix.FakeGmail([ProviderStatusError(403)]), tmp_path)
    result = fix.written_result(tmp_path)
    capsys.readouterr()

    status = report_main.main(["--result", str(result)])
    captured = capsys.readouterr()

    assert status == 3
    assert report_main.INCOMPLETE in captured.err
    assert "accepted       False" in captured.out


def test_a_delivery_record_is_written_beside_the_result(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    wired(monkeypatch, fix.FakeGmail(["17f0"]), tmp_path)
    result = fix.written_result(tmp_path)

    report_main.main(["--result", str(result)])

    written = tmp_path / "reporting" / f"delivery_{fix.GAME_ID}.json"
    assert written.exists()
    assert "17f0" in written.read_text(encoding="utf-8")


def test_the_command_refuses_a_call_that_names_no_result() -> None:
    with pytest.raises(SystemExit):
        report_main.parse_args([])


def test_the_command_is_runnable_as_a_module(tmp_path: Path) -> None:
    """`uv run python -m …report_main` really is the entry point.

    It runs with the credential variable **unset**, so what is proved is the
    refusal an operator meets first - and no provider is reachable from a test.
    """
    import os
    import subprocess
    import sys

    result = fix.written_result(tmp_path)
    environment = {name: value for name, value in os.environ.items() if name != TOKEN_PATH}
    finished = subprocess.run(
        [sys.executable, "-m", "mars777_police.report_main", "--result", str(result)],
        capture_output=True,
        text=True,
        check=False,
        env=environment,
    )

    assert finished.returncode == 2
    assert TOKEN_PATH in finished.stderr
    assert "Traceback" not in finished.stderr


def test_the_facade_reads_a_report_without_reaching_any_provider(tmp_path: Path) -> None:
    from mars777_police.sdk import AgentSdk

    result = fix.written_result(tmp_path)

    report = AgentSdk().read_game_report(result, tmp_path)

    assert report.game_id == fix.GAME_ID
    assert report.attachment == result.read_bytes()


def test_the_facade_sends_through_the_same_composition_the_command_uses(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from mars777_police.sdk import AgentSdk

    provider = fix.FakeGmail(["17f0"])
    wired(monkeypatch, provider, tmp_path)
    result = fix.written_result(tmp_path)

    outcome = AgentSdk().send_game_report(result, tmp_path)

    assert outcome.delivery.accepted is True
    assert outcome.delivery.provider_message_id == "17f0"
