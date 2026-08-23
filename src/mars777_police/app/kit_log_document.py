"""The per-sub-game log, rendered from the evidence the reference wire produced.

`finalized_log` builds the AUDITED-LOCAL state from an `OutboundEvidenceRuntime`
and an `AuditRuntime`. The gateway backends have neither: they seal into a
`KitRecordChain` and receive the peer's chain as a `KitAuditReveal`. Those are
the real artefacts of a played sub-game, so this renders the same log model from
them rather than re-deriving digests nobody exchanged.

**Both sides appear, each from its own evidence**, exactly as the counted
builder intends it: our turns from the chain we sealed, the peer's from the
chain it disclosed. Every entry carries the eight sealed members and, on the
reveal, the nonce - which is what a replayer needs to recompute the commitment
under `KIT_CORE_COMMITMENT_V1` and compare.

**`verified` is claimed only where it was measured.** We audit the peer's chain
and never our own, so our commit entries read `null` - the peer is the side that
checks them. The peer's read the verdict `peer_chain_verified` actually reached.

**A log is finalized only after the sub-game was audited.** A chain with no
disclosure beside it describes a sub-game that never settled, and is refused
rather than written as though it had.
"""

from typing import Any

from .audit_disclosure_writer import AuditDocument
from .kit_log_events import kit_commit_event, kit_reveal_event
from .kit_messages import KitAuditReveal, KitRecord
from .protocol_errors import LocalDefectError

Entries = list[dict[str, Any]]


def _steps(records: tuple[KitRecord, ...]) -> dict[int, KitRecord]:
    """Each record under the step it sealed, so both chains interleave by step."""
    found: dict[int, KitRecord] = {}
    for index, record in enumerate(records, start=1):
        step = record.payload.value.get("step")
        found[step if type(step) is int else index] = record
    return found


def kit_finalized_log(
    *,
    game_id: str,
    game_uid: str,
    sub_game: int,
    config_sha256: str,
    ours: tuple[KitRecord, ...],
    disclosure: KitAuditReveal | None,
    peer_verified: bool,
    result: str,
) -> AuditDocument:
    """Render the audited local log for one sub-game played on the reference wire."""
    if disclosure is None:
        raise LocalDefectError("a log is finalized only after this sub-game was audited")
    theirs = _steps(disclosure.records)
    mine = _steps(ours)
    entries: Entries = []
    for step in sorted(set(mine) | set(theirs)):
        record = mine.get(step)
        if record is not None:
            entries.append(kit_commit_event(record, None))
            entries.append(kit_reveal_event(record))
        other = theirs.get(step)
        if other is not None:
            entries.append(kit_commit_event(other, peer_verified))
            entries.append(kit_reveal_event(other))
    return {
        "game_id": game_id,
        "game_uid": game_uid,
        "sub_game": sub_game,
        "config_sha256": config_sha256,
        "entries": entries,
        "audit": {
            "peer_chain_reproduces": peer_verified,
            "peer_records": len(disclosure.records),
            "our_records": len(ours),
            "result": result,
        },
    }
