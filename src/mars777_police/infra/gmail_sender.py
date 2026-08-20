"""The Gmail adapter: one refresh, one send, both under the caller's gate.

Appendix A shows the flow with Google's own client libraries, and calls that
snippet an illustration of it. What the source **binds** is the mechanism, not
the package: the Gmail API (rule 32), OAuth 2.0 with the `gmail.send` scope and
nothing wider (rule 30, Appendix A §1.3), and `users.messages.send` carrying the
base64url-encoded MIME message.

**So this adapter speaks that API directly, over the standard library**, exactly
as `ngrok_ingress` already reads its provider. Three reasons, in order of
weight. The Google client builds its own retry engine and fetches a discovery
document of its own accord - a second limiter and a provider call outside the
Gatekeeper, which is precisely what Ch 9 §9.3.1 asks the Gatekeeper to prevent.
The exact outgoing request stays inspectable and golden-testable. And it adds no
dependency to install, which matters when independent verification is scarce.

**A token never reaches a message this module raises.** Failures name the status
and the endpoint; the `Authorization` header is built at the last moment and is
never logged, echoed or stored.
"""

import base64
import json
import urllib.error
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass, field
from urllib.parse import urlencode

from ..app.gatekeeper_retry import ProviderStatusError
from .gmail_credentials import GmailCredentials

SEND_ENDPOINT = "https://gmail.googleapis.com/gmail/v1/users/me/messages/send"
"""`users.messages.send` for the authenticated account - Appendix A's `userId="me"`."""

TIMEOUT_SECONDS = 30.0
"""Appendix F Table 19 row 6: the response time limit, NEGOTIABLE, example 30 s."""


class GmailSendError(ProviderStatusError):
    """A Gmail request failed. Carries a status and a wait, never a credential.

    A `ProviderStatusError` on purpose: that is the shape the Gatekeeper already
    classifies, so a Gmail `429` is honoured, backed off and bounded by the very
    policy `gatekeeper_retry` applies to every other provider - rather than by a
    second retry rule written here.
    """

    def __init__(self, message: str, status: int = 0, retry_after: float | None = None) -> None:
        super().__init__(status, retry_after)
        self.args = (message,)
        self.detail = message

    def __str__(self) -> str:
        return self.detail


def retry_after_of(failure: urllib.error.HTTPError) -> float | None:
    """The provider's own `Retry-After`, in seconds, when it sent a usable one.

    Ch 9's iron rule for `429` is to back off and *wait for the next window*, so
    a number the provider supplies is preferred over one we guessed. It is still
    clamped by the configured maximum in `gatekeeper_retry`: a provider asking
    for a day would otherwise stop this process by saying so.
    """
    raw = failure.headers.get("Retry-After") if failure.headers is not None else None
    if raw is None:
        return None
    try:
        seconds = float(str(raw).strip())
    except ValueError:
        return None
    return seconds if seconds > 0 else None


def post(url: str, body: bytes, headers: dict[str, str]) -> bytes:
    """POST *body* to *url* using the standard library, and return the response."""
    request = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            answer: bytes = response.read()
        return answer
    except urllib.error.HTTPError as failure:
        raise GmailSendError(
            f"{url} answered HTTP {failure.code}", failure.code, retry_after_of(failure)
        ) from None
    except OSError as failure:
        raise GmailSendError(f"{url} could not be reached: {type(failure).__name__}") from None


@dataclass(slots=True)
class GmailSender:
    """Sends one already-built message as the authenticated Gmail account."""

    credentials: GmailCredentials
    poster: Callable[[str, bytes, dict[str, str]], bytes] = post
    endpoint: str = SEND_ENDPOINT
    _access: str | None = field(default=None, repr=False)

    def _refresh(self) -> str:
        """Exchange the refresh token for an access token, and keep it in memory."""
        body = urlencode(self.credentials.refresh_form()).encode()
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        answer = _decode(self.poster(self.credentials.token_uri, body, headers))
        token = answer.get("access_token")
        if not isinstance(token, str) or not token:
            raise GmailSendError("the token endpoint returned no access token")
        self._access = token
        return token

    def send(self, message: bytes) -> str:
        """Send *message* and return the identifier Gmail assigned it."""
        raw = base64.urlsafe_b64encode(message).decode("ascii")
        body = json.dumps({"raw": raw}, separators=(",", ":")).encode()
        headers = {
            "Authorization": f"Bearer {self._access or self._refresh()}",
            "Content-Type": "application/json",
        }
        answer = _decode(self.poster(self.endpoint, body, headers))
        identifier = answer.get("id")
        if not isinstance(identifier, str) or not identifier:
            raise GmailSendError("Gmail accepted the request but named no message")
        return identifier


def _decode(body: bytes) -> dict[str, object]:
    """Parse a provider response strictly. A body that is not an object is a failure."""
    try:
        answer = json.loads(body.decode())
    except (UnicodeDecodeError, json.JSONDecodeError) as failure:
        raise GmailSendError("the provider returned a body that is not JSON") from failure
    if not isinstance(answer, dict):
        raise GmailSendError("the provider returned a body that is not an object")
    return answer
