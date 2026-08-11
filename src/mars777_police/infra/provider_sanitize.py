"""Keeping provider diagnostics out of everything that matters.

`PRD05-FR-051` forbids credentials in logs and error messages, and `FR-065`
forbids a network failure being reported as an integrity failure. A tunnel agent
writes whatever it likes to its own stream, so the project treats every provider
line as untrusted text: a line is either reduced to a redaction marker or
truncated, and it is never forwarded to a peer.

The match is deliberately over **field-name hints** rather than value shapes. A
regex for "things that look like a token" fails open on the one token that does
not look like the others; a line mentioning `authtoken` at all is simply not
worth keeping.
"""

from typing import Final

_HINTS: Final[tuple[str, ...]] = (
    "authtoken",
    "auth_token",
    "auth-token",
    "api_key",
    "apikey",
    "api-key",
    "credential",
    "password",
    "secret",
    "bearer",
    "authorization",
    "cookie",
)
REDACTED: Final[str] = "<redacted provider diagnostic>"
MAX_LENGTH: Final[int] = 200


def sanitize(text: str) -> str:
    """Return a form of *text* safe to keep in a local diagnostic.

    A line mentioning any credential-shaped field name is discarded entirely;
    anything else is stripped and truncated, so an agent that decides to dump
    its environment cannot fill our logs with it.
    """
    if any(hint in text.lower() for hint in _HINTS):
        return REDACTED
    return text.strip()[:MAX_LENGTH]
