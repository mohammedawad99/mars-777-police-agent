"""The exact request that would leave this machine, without one leaving it.

Appendix A fixes the mechanism: OAuth 2.0 with the `gmail.send` scope and
nothing wider, and `users.messages.send` carrying the base64url-encoded MIME
message. There is no live account here, so the seam under test is the adapter's
own HTTP call - captured, asserted, and never made.
"""

import base64
import json

import pytest

from mars777_police.infra.gmail_credentials import GmailCredentials
from mars777_police.infra.gmail_sender import SEND_ENDPOINT, GmailSender, GmailSendError

TOKEN_URI = "https://oauth2.googleapis.com/token"


def credentials() -> GmailCredentials:
    return GmailCredentials("client-id", "client-secret", "refresh-token")


class Recorder:
    """Records every request the adapter makes and answers as instructed."""

    def __init__(self, *answers: object) -> None:
        self.answers = list(answers)
        self.calls: list[tuple[str, bytes, dict[str, str]]] = []

    def __call__(self, url: str, body: bytes, headers: dict[str, str]) -> bytes:
        self.calls.append((url, body, headers))
        answer = self.answers.pop(0)
        if isinstance(answer, BaseException):
            raise answer
        return json.dumps(answer).encode()


def test_a_send_refreshes_once_and_then_posts_to_the_documented_endpoint() -> None:
    poster = Recorder({"access_token": "at-1"}, {"id": "17f0"})

    identifier = GmailSender(credentials(), poster).send(b"RAW MESSAGE")

    assert identifier == "17f0"
    assert poster.calls[0][0] == TOKEN_URI
    assert poster.calls[1][0] == SEND_ENDPOINT


def test_the_refresh_body_is_the_oauth_refresh_grant_and_nothing_else() -> None:
    poster = Recorder({"access_token": "at-1"}, {"id": "1"})

    GmailSender(credentials(), poster).send(b"RAW")

    body = poster.calls[0][1].decode()
    assert "grant_type=refresh_token" in body
    assert poster.calls[0][2]["Content-Type"] == "application/x-www-form-urlencoded"


def test_the_send_carries_a_bearer_header_whose_value_is_never_asserted() -> None:
    poster = Recorder({"access_token": "at-1"}, {"id": "1"})

    GmailSender(credentials(), poster).send(b"RAW")

    headers = poster.calls[1][2]
    assert headers["Authorization"].startswith("Bearer ")
    assert headers["Content-Type"] == "application/json"


def test_the_message_travels_base64url_encoded_and_round_trips_unchanged() -> None:
    poster = Recorder({"access_token": "at-1"}, {"id": "1"})
    original = b"To: someone@example.test\r\n\r\nbody with + and / bytes \xf0\x9f\x99\x82"

    GmailSender(credentials(), poster).send(original)

    raw = json.loads(poster.calls[1][1])["raw"]
    assert base64.urlsafe_b64decode(raw) == original
    assert "+" not in raw and "/" not in raw


def test_the_access_token_is_reused_rather_than_refreshed_for_every_send() -> None:
    poster = Recorder({"access_token": "at-1"}, {"id": "1"}, {"id": "2"})
    sender = GmailSender(credentials(), poster)

    sender.send(b"one")
    sender.send(b"two")

    assert [call[0] for call in poster.calls].count(TOKEN_URI) == 1


def test_a_token_endpoint_that_answers_without_a_token_is_a_failure() -> None:
    poster = Recorder({"error": "invalid_grant"})

    with pytest.raises(GmailSendError, match="no access token"):
        GmailSender(credentials(), poster).send(b"RAW")


def test_a_provider_body_that_is_not_json_is_refused_rather_than_guessed() -> None:
    class Garbage:
        def __call__(self, url: str, body: bytes, headers: dict[str, str]) -> bytes:
            return b"<html>not json</html>"

    with pytest.raises(GmailSendError, match="not JSON"):
        GmailSender(credentials(), Garbage()).send(b"RAW")


def test_a_provider_body_that_is_json_but_not_an_object_is_refused() -> None:
    class Listy:
        def __call__(self, url: str, body: bytes, headers: dict[str, str]) -> bytes:
            return b"[1, 2, 3]"

    with pytest.raises(GmailSendError, match="not an object"):
        GmailSender(credentials(), Listy()).send(b"RAW")


def test_an_accepted_request_that_names_no_message_is_still_a_failure() -> None:
    poster = Recorder({"access_token": "at-1"}, {"labelIds": []})

    with pytest.raises(GmailSendError, match="named no message"):
        GmailSender(credentials(), poster).send(b"RAW")


def test_a_failure_message_never_carries_the_credential_it_used() -> None:
    poster = Recorder({"access_token": "super-secret-token"}, GmailSendError("boom", 500))

    with pytest.raises(GmailSendError) as failure:
        GmailSender(credentials(), poster).send(b"RAW")

    rendered = f"{failure.value!r} {failure.value}"
    for secret in ("super-secret-token", "client-secret", "refresh-token"):
        assert secret not in rendered
