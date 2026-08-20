"""The one path that would touch a real mailbox, and why it never runs by itself.

A real send is not something a test suite may decide to do: it mails the
lecturer. So this file requires an explicit opt-in **and** a credential **and**
an explicit recipient override, and it is skipped when any of the three is
absent - which is always, on CI and on a developer machine that merely happens
to have a token lying about.

The default state of this file is therefore `NOT_RUN`, and that is the correct
state until an operator authorises one send.
"""

import os

import pytest

from mars777_police.infra.gmail_credentials import TOKEN_PATH

LIVE_OPT_IN = "MARS777_RUN_LIVE_GMAIL"
LIVE_RECIPIENT = "MARS777_LIVE_GMAIL_RECIPIENT"


def authorised() -> bool:
    """All three signals, deliberately: none of them alone permits a send."""
    return (
        os.environ.get(LIVE_OPT_IN) == "1"
        and bool(os.environ.get(TOKEN_PATH, "").strip())
        and bool(os.environ.get(LIVE_RECIPIENT, "").strip())
    )


live = pytest.mark.skipif(
    not authorised(),
    reason=(
        "the live Gmail smoke needs an explicit operator authorisation:"
        f" {LIVE_OPT_IN}=1 plus {TOKEN_PATH} plus {LIVE_RECIPIENT}"
    ),
)


def test_a_credential_alone_never_authorises_a_real_send(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """No skip: this is the property that keeps every other run safe."""
    monkeypatch.setenv(TOKEN_PATH, "/tmp/whatever/token.json")
    monkeypatch.delenv(LIVE_OPT_IN, raising=False)
    monkeypatch.delenv(LIVE_RECIPIENT, raising=False)

    assert authorised() is False


def test_the_opt_in_alone_never_authorises_a_real_send(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(LIVE_OPT_IN, "1")
    monkeypatch.delenv(TOKEN_PATH, raising=False)
    monkeypatch.delenv(LIVE_RECIPIENT, raising=False)

    assert authorised() is False


def test_all_three_signals_together_are_what_authorise_one(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(LIVE_OPT_IN, "1")
    monkeypatch.setenv(TOKEN_PATH, "/tmp/whatever/token.json")
    monkeypatch.setenv(LIVE_RECIPIENT, "someone@example.test")

    assert authorised() is True


@live
def test_one_authorised_message_reaches_gmail() -> None:
    """The only test in this project that would send real mail. Never on CI.

    It sends to the operator's **own** explicitly supplied address rather than
    to the lecturer's, and it carries a clearly-labelled test payload, so an
    authorised smoke can never be mistaken for a counted game report.
    """
    from mars777_police.app.report_message import message_bytes
    from mars777_police.app.report_values import GameReport
    from mars777_police.infra.gmail_credentials import credentials_path, load_credentials
    from mars777_police.infra.gmail_sender import GmailSender

    report = GameReport(
        game_id="LIVE-SMOKE-NOT-A-GAME",
        group_id="mars777",
        role="police",
        result_sha256="0" * 64,
        attachment_name="live_smoke_not_a_result.json",
        attachment=b'{"live_smoke": true, "counted": false}',
    )
    message = message_bytes(report).replace(
        b"rmisegal+uoh26finalgame@gmail.com", os.environ[LIVE_RECIPIENT].encode()
    )

    identifier = GmailSender(load_credentials(credentials_path())).send(message)

    assert identifier
