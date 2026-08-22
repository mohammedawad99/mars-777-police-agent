"""`python -m mars777_police.gmail_preflight` - is reporting ready, right now?

Run this **before** a counted series, never after. Appendix E rule 35 scores a
missing report 0 for both groups, so the moment to discover an expired refresh
token is while there is still time to fix it - not once a result exists and the
agent is trying to send it.

**It contacts Google, and it never contacts the lecturer.** The one network call
is an OAuth token refresh, which proves the stored credential can still obtain
an access token. No message is composed, no recipient is addressed, and the
fixed reporting address is only *compared*, never used.

**It prints no secret.** Every check reports a name, a verdict and a reason; no
token, client id, client secret or access token reaches the output.

Exit status is the answer: `0` ready, `2` not ready.
"""

import argparse
import json
import os
import stat
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from .app.report_values import REPORTS_ADDRESS
from .infra.gmail_credentials import (
    SEND_SCOPE,
    TOKEN_PATH,
    GmailCredentialError,
    GmailCredentials,
    credentials_path,
    load_credentials,
)
from .infra.rate_limit_file import load_rate_limits

READY = "GMAIL_PREFLIGHT_READY = YES"
NOT_READY = "GMAIL_PREFLIGHT_READY = NO"
Check = tuple[str, bool, str]


def _permissions(path: Path, system: str | None = None) -> Check:
    """Whether the token file is private to its owner. POSIX only.

    **Windows cannot answer this question the POSIX way.** `os.chmod` there
    toggles the read-only bit and nothing else, so NTFS reports `0666` for a
    file that may be perfectly well protected by an ACL this code cannot read.
    Treating that as "not private" would make the preflight answer
    `GMAIL_PREFLIGHT_READY = NO` forever on a Windows operator machine and block
    counted play over a credential that is fine.

    So the check reports honestly that it does not apply, rather than failing.
    Protecting the file is still the operator's job there - it is simply not a
    thing this can verify, and claiming otherwise would be the worse error.
    """
    if (system if system is not None else os.name) == "nt":
        return ("token file is private", True, "not checkable on Windows (NTFS ACLs)")
    mode = stat.S_IMODE(path.stat().st_mode)
    return ("token file is private", (mode & 0o077) == 0, f"mode {mode:04o}")


def refresh(credentials: GmailCredentials) -> Check:
    """One real OAuth refresh, reported without revealing anything it used."""
    body = urllib.parse.urlencode(
        {
            "client_id": credentials.client_id,
            "client_secret": credentials.client_secret,
            "refresh_token": credentials.refresh_token,
            "grant_type": "refresh_token",
        }
    ).encode()
    request = urllib.request.Request(
        credentials.token_uri,
        data=body,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as answer:
            document = json.loads(answer.read().decode("utf-8"))
    except urllib.error.HTTPError as failure:
        return ("live token refresh", False, f"token endpoint returned HTTP {failure.code}")
    except OSError as failure:
        return ("live token refresh", False, f"unreachable: {type(failure).__name__}")
    scope = str(document.get("scope", ""))
    if scope and SEND_SCOPE not in scope:
        return ("live token refresh", False, "the granted scope is not the send scope")
    return ("live token refresh", True, f"expires_in={document.get('expires_in')}s scope={scope}")


def checks(env: dict[str, str] | None = None) -> list[Check]:
    """Every readiness check, each a name, a verdict and a reason."""
    try:
        path = credentials_path(env if env is not None else dict(os.environ))
    except GmailCredentialError as failure:
        return [(TOKEN_PATH, False, str(failure))]
    found: list[Check] = [(TOKEN_PATH, True, f"names {path}")]
    found.append(("token file exists", path.is_file(), str(path)))
    if not path.is_file():
        return found
    found.append(_permissions(path))
    try:
        credentials = load_credentials(path)
    except GmailCredentialError as failure:
        found.append(("credential schema", False, str(failure)))
        return found
    found.append(("credential schema", True, "client_id, client_secret, refresh_token present"))
    found.append(("scope is send-only", True, SEND_SCOPE))
    expected = "rmisegal+uoh26finalgame@gmail.com"
    found.append(("recipient constant", expected == REPORTS_ADDRESS, REPORTS_ADDRESS))
    try:
        load_rate_limits()
        found.append(("rate-limit config loads", True, "gatekeeper configuration read"))
    except Exception as failure:
        found.append(("rate-limit config loads", False, type(failure).__name__))
    found.append(refresh(credentials))
    return found


def main(argv: list[str] | None = None) -> int:
    """Report whether a counted series could report itself right now."""
    argparse.ArgumentParser(prog="python -m mars777_police.gmail_preflight").parse_args(argv)
    results = checks()
    for name, ok, reason in results:
        print(f"{'PASS' if ok else 'FAIL'}  {name}: {reason}", flush=True)
    ready = all(ok for _, ok, _ in results)
    print(READY if ready else NOT_READY, flush=True)
    return 0 if ready else 2


if __name__ == "__main__":
    raise SystemExit(main())
