"""A test-only record of when the synthetic opponent's inbound handlers ran.

Windows exact-SHA CI stalls in g01: the real CLI waits thirty seconds for its
acknowledgement to be answered and the opponent never times out on anything of
its own. Three explanations survived the last diagnostic, and they differ only
in what happened *inside the peer* - whether the handler for that request never
began, began and stalled, or began and finished while its answer never came
back. None of that is visible from either side's stack.

So the opponent writes down when it enters and leaves those handlers. Nothing
here belongs to the shipped CLI: the real process stays byte-identical, and
this is installed by the **synthetic, non-counted** opponent on itself.

**Why three families and not just the acknowledgement.** The acknowledgement
alone cannot separate "never arrived" from "arrived, answered, answer lost":
both leave the opponent's last acknowledgement looking complete. The turn
sequence does separate them. If the last acknowledgement completed and nothing
inbound follows it, the real CLI never learned the answer - it would otherwise
have revealed, and that reveal would be here. If something inbound *does*
follow, the answer did arrive and the request finally waited on is a later one
that left no trace at all. Commitment and reveal are therefore recorded too,
and nothing else is.

**Only safe metadata is written.** `(sub_game, step)` is the transmitted turn
cursor - a projection the wire already carries - and an error is recorded by
its class name. No secret, no auth proof, no nonce, no digest, no payload.
"""

import json
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

ACKNOWLEDGEMENT = "acknowledgement"
COMMITMENT = "commitment"
REVEAL = "reveal"

TRACED = {
    "on_commitment": COMMITMENT,
    "on_acknowledgement": ACKNOWLEDGEMENT,
    "on_reveal": REVEAL,
}
"""The inbound operations recorded, and the family each one is written under."""


class HandlerTrace:
    """Append-only JSONL, one line per handler boundary, flushed as it is made.

    Written a line at a time rather than through a held buffer: the process
    whose behaviour is in question is the one that has been dying, and a record
    it never flushed would be the record worth having. The volume is bounded by
    the turns of one sub-game, so the cost is not on any hot path.
    """

    def __init__(self, path: Path) -> None:
        self.path = path
        self.sequence = 0

    def event(self, event: str, family: str, **fields: object) -> None:
        """Write one boundary, with a local sequence and a monotonic reading."""
        self.sequence += 1
        record: dict[str, object] = {
            "event": event,
            "family": family,
            "seq": self.sequence,
            "monotonic_ns": time.monotonic_ns(),
            **fields,
        }
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record) + "\n")


def traced(original: Callable[..., Any], family: str, trace: HandlerTrace) -> Callable[..., Any]:
    """Wrap one inbound operation transparently: it decides nothing.

    The original is called exactly once with exactly its own arguments, its
    return value is passed back unchanged and its exception is re-raised
    unchanged. There is no sleep, no retry, no lock and no barrier here, so the
    two processes are never serialized and the race cannot be observed away.
    """

    def wrapper(operations: object, message: object, session: object) -> Any:
        cursor = getattr(message, "cursor", None)
        where = {
            "sub_game": getattr(cursor, "sub_game", None),
            "step": getattr(cursor, "step", None),
        }
        trace.event("inbound_start", family, **where)
        try:
            result = original(operations, message, session)
        except BaseException as failure:
            trace.event("inbound_error", family, error_type=type(failure).__name__, **where)
            raise
        trace.event("inbound_success", family, **where)
        return result

    return wrapper


def install(operations: type, trace: HandlerTrace) -> None:
    """Record the three turn operations on *operations*, in this process only."""
    for name, family in TRACED.items():
        setattr(operations, name, traced(getattr(operations, name), family, trace))


def events(path: Path) -> list[dict[str, Any]]:
    """Read the trace back, tolerating a final line a dying process cut short."""
    if not path.exists():
        return []
    found = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            found.append(json.loads(line))
        except ValueError:
            continue
    return found


def classify(found: list[dict[str, Any]]) -> str:
    """Name which of the three explanations the trace actually supports.

    The rules are only the ones the evidence can carry. An acknowledgement that
    began and never ended is a stalled handler. One that ended with nothing
    inbound after it means the answer never got home, because the real CLI
    would otherwise have revealed. One that ended with inbound work after it
    means that answer *did* get home and the request finally waited on never
    reached a handler at all. A handler that raised should have produced an
    error for the caller rather than a silence, so it is not classified here.
    """
    acknowledgements = [one for one in found if one.get("family") == ACKNOWLEDGEMENT]
    if not acknowledgements:
        return "H1 - no acknowledgement ever reached the instrumented handler"
    last = acknowledgements[-1]
    if last.get("event") == "inbound_start":
        return "H2 - the last acknowledgement handler began and never returned"
    if last.get("event") == "inbound_error":
        return "HX - the last acknowledgement handler raised; a caller should have seen that"
    after = [one for one in found if int(one.get("seq", 0)) > int(last.get("seq", 0))]
    if not after:
        return "H3 - the last acknowledgement completed and nothing inbound followed it"
    return (
        "H1 - the last acknowledgement completed and inbound work followed it,"
        " so the one finally awaited never reached a handler"
    )


def summary(path: Path, keep: int = 12) -> str:
    """The tail of the trace, what it implies, and the numbers behind it."""
    found = events(path)
    acknowledgements = [one for one in found if one.get("family") == ACKNOWLEDGEMENT]
    starts = [one for one in acknowledgements if one.get("event") == "inbound_start"]
    done = [one for one in acknowledgements if one.get("event") != "inbound_start"]
    lines = [
        f"  opponent handler trace: {path}",
        f"    events: {len(found)} total, {len(acknowledgements)} acknowledgement",
        f"    acknowledgement starts: {len(starts)}, completed: {len(done)},"
        f" unmatched: {len(starts) - len(done)}",
        f"    last acknowledgement start: {starts[-1] if starts else 'none'}",
        f"    last acknowledgement completed: {done[-1] if done else 'none'}",
        f"    CLASSIFICATION: {classify(found)}",
        f"    last {keep} events:",
    ]
    lines.extend(f"      {one}" for one in found[-keep:])
    return "\n".join(lines)
