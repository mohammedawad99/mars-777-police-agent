"""Where delivery status is written, and why it is not a game artifact.

Appendix F Table 20 fixes the official set: one declaration, one config and one
log per sub-game, and one result - fourteen files for a six-sub-game series. A
report's *delivery status* is not one of them. It says what a mail provider did,
which is a fact about our outbox rather than about the game, and adding it to
the official namespace would make a graded artifact set depend on whether an
email happened to go out.

So it is written **beside** the official files, under its own name, and a test
holds the official count at exactly fourteen.

**No credential is ever recorded.** The document carries the report identity,
the operation, whether the provider accepted, and the provider's own message id
- which is not a secret and is what an operator needs to find the message again.
It carries no token, no `Authorization` header, no client secret, and no body.
"""

import json
from pathlib import Path

from ..app.report_values import ReportDelivery

EVIDENCE_DIRECTORY = "reporting"
"""Deliberately outside the official artifact namespace, and named for what it is."""


def evidence_name(game_id: str) -> str:
    """`delivery_<game_id>.json` - one per game, never `result_`/`log_`/`config_`."""
    return f"delivery_{game_id}.json"


def evidence_document(delivery: ReportDelivery, game_id: str, operation: str) -> dict[str, object]:
    """The safe record of one delivery attempt, with nothing sensitive in it."""
    return {
        "game_id": game_id,
        "operation": operation,
        "report_identity": delivery.identity,
        "attempted": True,
        "provider_accepted": delivery.accepted,
        "provider_message_id": delivery.provider_message_id,
        "failure": delivery.failure,
    }


def write_evidence(root: Path, game_id: str, document: dict[str, object]) -> Path:
    """Write the delivery record under *root*, and say where it went."""
    directory = root / EVIDENCE_DIRECTORY
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / evidence_name(game_id)
    target.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return target


def accepted_identity(root: Path, game_id: str) -> str | None:
    """The report identity this machine already delivered for *game_id*, if any.

    The durable half of "send once". `ReportService` refuses a second send inside
    one process; this survives the process, because a restarted agent that
    mailed the lecturer again would risk the contradictory-report penalty in
    Appendix E rule 35.

    Returns the **identity** rather than a boolean on purpose: a different agreed
    result under the same `game_id` is a different report and must still be sent,
    so the caller compares digests rather than trusting a file name.

    An absent, unreadable or not-accepted record all mean *not delivered*. The
    failure a corrupt file could cause is a missing report, which is the worse
    of the two errors, so it is never inferred as a delivery.
    """
    target = root / EVIDENCE_DIRECTORY / evidence_name(game_id)
    try:
        document = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if document.get("provider_accepted") is not True:
        return None
    identity = document.get("report_identity")
    return identity if isinstance(identity, str) else None
