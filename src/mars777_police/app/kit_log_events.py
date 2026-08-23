"""One log entry built from what the reference wire actually sealed.

`log_events` renders entries from `SealedTurnRecord`, which carries the counted
scheme's eight-member sealed record. The reference wire seals something else:
`kit_payload` commits `{step, sub_game, role, move, intent, hint, position,
barriers}` under `KIT_CORE_COMMITMENT_V1`. The two are different constructions
over different bytes, so a log rendered from one cannot be replayed against a
digest produced by the other.

**The log records what crossed the wire, never a re-derivation of it.** Our
opponent received these commitments, re-hashed them and reproduced six audits
against them. Rendering the counted scheme's digests instead would put values in
an official record that no opponent ever saw - which is manufacturing evidence,
whatever the intent.

**`config_sha256` is deliberately absent from the state block.** The counted
sealed state includes it because the counted commitment seals it; the KIT
commitment does not. Writing it inside `state` would hand a replayer a state
that cannot reproduce the digest beside it. It stays at the log's top level,
where it is a fact about the sub-game rather than a claim about what was sealed.
"""

from typing import Any

from .kit_messages import KitRecord

COMMIT = "commit"
REVEAL = "reveal"
SEALED = ("step", "sub_game", "role", "move", "intent", "hint", "position", "barriers")
"""Exactly what `kit_payload` commits, in the order it commits it."""


def sealed_members(record: KitRecord) -> dict[str, object]:
    """The committed payload, read back as it was sealed and not rebuilt."""
    payload = record.payload.value
    return {name: payload[name] for name in SEALED if name in payload}


def kit_state(record: KitRecord) -> dict[str, object]:
    """The own-known snapshot the KIT commitment sealed, and nothing more."""
    members = sealed_members(record)
    return {
        "self_pos": members.get("position"),
        "barriers": members.get("barriers", []),
        "step": members.get("step"),
        "role": members.get("role"),
    }


def kit_entry(record: KitRecord) -> dict[str, object]:
    """One turn in the shared eight-member log shape, from the KIT record."""
    members = sealed_members(record)
    return {
        "step": members.get("step"),
        "sub_game": members.get("sub_game"),
        "role": members.get("role"),
        "move": members.get("move"),
        "intent": members.get("intent"),
        "hint": members.get("hint"),
        "commit": record.commit.value,
        "state": kit_state(record),
    }


def kit_commit_event(record: KitRecord, verified: bool | None) -> dict[str, Any]:
    """A commitment event. `verified` is claimed only where it was measured."""
    entry = dict(kit_entry(record))
    entry["phase"], entry["verified"] = COMMIT, verified
    return entry


def kit_reveal_event(record: KitRecord) -> dict[str, Any]:
    """The matching reveal, carrying the nonce that opens the commitment."""
    entry = dict(kit_entry(record))
    entry["phase"], entry["verified"] = REVEAL, None
    entry["nonce"] = record.nonce
    return entry
