"""Loading the OAuth material Appendix A produces, and refusing to print it.

Appendix A §1.5 says the first authorisation run writes `token.json`, holding a
short-lived Access Token beside a long-lived Refresh Token, and that the Refresh
Token is what lets the agent report autonomously for months without a human. So
this module reads that file - the operator's own, never committed, already in
`.gitignore` per Appendix A's own instruction and rule 40 - and exchanges the
refresh token for an access token when one is needed.

**Least privilege, checked rather than assumed.** Appendix A §1.3 and Appendix E
rule 30 require the scope `gmail.send` and nothing wider; a token file that
claims `gmail.modify` or full mailbox access is refused here rather than used.

**No secret is ever rendered.** The values are wrapped so `repr` and `str` show
nothing, refusals name the *file* and the *field* and never a value, and no
token reaches a log line, an exception message or an artifact.
"""

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Final

TOKEN_PATH: Final[str] = "MARS777_GMAIL_TOKEN"
"""Where the operator keeps the `token.json` Appendix A's first run produced."""

SEND_SCOPE: Final[str] = "https://www.googleapis.com/auth/gmail.send"
REQUIRED: Final[tuple[str, ...]] = ("client_id", "client_secret", "refresh_token")


class GmailCredentialError(Exception):
    """The reporting credential is absent, unreadable, or wider than send-only.

    Local by construction: no peer causes it and its message names no value.
    """


@dataclass(frozen=True, slots=True)
class GmailCredentials:
    """The refresh material for one send-only Gmail identity."""

    client_id: str = field(repr=False)
    client_secret: str = field(repr=False)
    refresh_token: str = field(repr=False)
    token_uri: str = "https://oauth2.googleapis.com/token"

    def __repr__(self) -> str:
        return "GmailCredentials(<withheld>)"

    def __str__(self) -> str:
        return "<withheld>"

    def refresh_form(self) -> dict[str, str]:
        """The exact form body an OAuth 2.0 refresh exchange requires."""
        return {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": self.refresh_token,
            "grant_type": "refresh_token",
        }


def _scopes(document: dict[str, object], source: Path) -> None:
    raw = document.get("scopes")
    if raw is None:
        return
    if not isinstance(raw, list) or [one for one in raw if one != SEND_SCOPE]:
        raise GmailCredentialError(
            f"{source} grants a scope wider than send-only; Appendix E rule 30 permits"
            f" exactly {SEND_SCOPE}"
        )


def credentials_path(env: dict[str, str] | None = None) -> Path:
    """Where the credential lives, or a refusal naming the variable to set."""
    source = os.environ if env is None else env
    value = source.get(TOKEN_PATH, "").strip()
    if not value:
        raise GmailCredentialError(
            f"{TOKEN_PATH} is required and must name the token.json Appendix A produced"
        )
    return Path(value)


def load_credentials(path: Path) -> GmailCredentials:
    """Read *path* into credentials, or refuse with a reason that names no value."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as failure:
        raise GmailCredentialError(f"cannot read the Gmail credential file {path}") from failure
    try:
        document = json.loads(text)
    except json.JSONDecodeError as failure:
        raise GmailCredentialError(f"{path} is not valid JSON") from failure
    if not isinstance(document, dict):
        raise GmailCredentialError(f"{path} is not a credential object")
    missing = [name for name in REQUIRED if not isinstance(document.get(name), str)]
    if missing:
        raise GmailCredentialError(f"{path} is missing: {', '.join(sorted(missing))}")
    _scopes(document, path)
    uri = document.get("token_uri")
    return GmailCredentials(
        client_id=str(document["client_id"]),
        client_secret=str(document["client_secret"]),
        refresh_token=str(document["refresh_token"]),
        token_uri=uri if isinstance(uri, str) and uri else "https://oauth2.googleapis.com/token",
    )
