"""The adapter's own HTTP call, exercised without a single packet leaving.

`post` is the one function in the reporting path that would touch a socket, so
the standard-library call it makes is replaced and every branch it can take is
run: an accepted body, a status the provider refused with, a `Retry-After` it
supplied, and a transport that never answered.
"""

import io
import urllib.error
import urllib.request

import pytest

from mars777_police.infra.gmail_sender import GmailSendError, post, retry_after_of


class Answer:
    """The context manager `urlopen` returns, holding one body."""

    def __init__(self, body: bytes) -> None:
        self.body = body

    def __enter__(self) -> "Answer":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def read(self) -> bytes:
        return self.body


def http_error(status: int, headers: dict[str, str] | None = None) -> urllib.error.HTTPError:
    return urllib.error.HTTPError(
        "https://gmail.googleapis.test/send", status, "refused", headers or {}, io.BytesIO(b"")
    )


def test_an_accepted_request_returns_the_body_unchanged(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(urllib.request, "urlopen", lambda *a, **k: Answer(b'{"id": "1"}'))

    assert post("https://x.test", b"{}", {}) == b'{"id": "1"}'


def test_a_refused_status_becomes_a_typed_failure_carrying_that_status(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def refuse(*args: object, **kwargs: object) -> Answer:
        raise http_error(429)

    monkeypatch.setattr(urllib.request, "urlopen", refuse)

    with pytest.raises(GmailSendError) as failure:
        post("https://x.test", b"{}", {})

    assert failure.value.status == 429
    assert "429" in str(failure.value)


def test_a_provider_supplied_retry_after_is_carried_onto_the_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def refuse(*args: object, **kwargs: object) -> Answer:
        raise http_error(429, {"Retry-After": "42"})

    monkeypatch.setattr(urllib.request, "urlopen", refuse)

    with pytest.raises(GmailSendError) as failure:
        post("https://x.test", b"{}", {})

    assert failure.value.retry_after == 42.0


def test_a_transport_that_never_answered_is_a_failure_naming_no_credential(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def refuse(*args: object, **kwargs: object) -> Answer:
        raise TimeoutError("timed out")

    monkeypatch.setattr(urllib.request, "urlopen", refuse)

    with pytest.raises(GmailSendError, match="could not be reached"):
        post("https://x.test", b"{}", {"Authorization": "Bearer secret-value"})


@pytest.mark.parametrize(
    ("header", "expected"),
    [
        ({}, None),
        ({"Retry-After": "Wed, 21 Oct 2026 07:28:00 GMT"}, None),
        ({"Retry-After": "0"}, None),
        ({"Retry-After": " 12 "}, 12.0),
    ],
)
def test_only_a_usable_retry_after_is_taken_from_the_provider(
    header: dict[str, str], expected: float | None
) -> None:
    assert retry_after_of(http_error(429, header)) == expected
