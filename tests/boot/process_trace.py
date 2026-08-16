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

import itertools
import json
import time
from collections.abc import Awaitable, Callable
from contextvars import ContextVar
from pathlib import Path
from typing import Any

ACKNOWLEDGEMENT = "acknowledgement"
COMMITMENT = "commitment"
REVEAL = "reveal"

REQUEST_ID: ContextVar[int | None] = ContextVar("diagnostic_request_id", default=None)
"""Set by the ASGI wrapper, read wherever the execution context still carries it.

It is expected to be **absent** below the transport. The server session hands a
decoded request to a task started from its own receive loop, not from the task
serving the HTTP request, so the context copied into the tool is that loop's -
not this one's. A null id there is evidence about the architecture, not a
failure of the instrument, and correlation then rests on order instead.
"""

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


class Timed:
    """ASGI middleware that times a request and touches nothing else.

    It reads the status off `http.response.start` as it goes past and forwards
    every message unchanged. Nothing is buffered and no body is consumed, so a
    streamed response still streams: the point is to know *when* the server
    application received a request relative to when the tool below it ran.
    """

    def __init__(self, app: Any, trace: HandlerTrace) -> None:
        self.app, self.trace = app, trace
        self.counter = itertools.count(1)

    async def __call__(self, scope: Any, receive: Any, send: Any) -> None:
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return
        request_id = next(self.counter)
        seen: list[int] = []

        async def watched(message: Any) -> None:
            if message.get("type") == "http.response.start":
                seen.append(int(message["status"]))
            await send(message)

        self.trace.event(
            "asgi_start",
            "http",
            request_id=request_id,
            method=scope.get("method"),
            path=scope.get("path"),
        )
        token = REQUEST_ID.set(request_id)
        try:
            await self.app(scope, receive, watched)
        except BaseException as failure:
            self.trace.event(
                "asgi_error", "http", request_id=request_id, error_type=type(failure).__name__
            )
            raise
        else:
            self.trace.event(
                "asgi_end", "http", request_id=request_id, status=seen[0] if seen else None
            )
        finally:
            REQUEST_ID.reset(token)


def timed_async(
    original: Callable[..., Awaitable[Any]], event: str, family: str, trace: HandlerTrace
) -> Callable[..., Awaitable[Any]]:
    """Bracket one awaited callable, carrying whatever request id is in scope."""

    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        trace.event(f"{event}_start", family, request_id=REQUEST_ID.get())
        try:
            result = await original(*args, **kwargs)
        except BaseException as failure:
            trace.event(
                f"{event}_error",
                family,
                request_id=REQUEST_ID.get(),
                error_type=type(failure).__name__,
            )
            raise
        trace.event(f"{event}_success", family, request_id=REQUEST_ID.get())
        return result

    return wrapper


def timed_router(original: Callable[..., Any], trace: HandlerTrace) -> Callable[..., Any]:
    """Bracket the turn router, naming only the request kind it dispatches on."""

    def wrapper(operations: Any, request: Any, session: Any) -> Any:
        kind = getattr(request, "kind", None)
        trace.event("router_start", str(kind), request_id=REQUEST_ID.get())
        try:
            result = original(operations, request, session)
        except BaseException as failure:
            trace.event(
                "router_error",
                str(kind),
                request_id=REQUEST_ID.get(),
                error_type=type(failure).__name__,
            )
            raise
        trace.event("router_success", str(kind), request_id=REQUEST_ID.get())
        return result

    return wrapper


def install_dispatch(trace: HandlerTrace) -> None:
    """Time the whole opponent ingress, from ASGI arrival down to the handler.

    Four seams, each the narrowest one reachable without touching `src`: the
    ASGI application, the tool body's first await, the turn router, and the
    handler the previous checkpoint already traced. Between them they say which
    interval holds the thirty seconds.

    The middleware is added to the real Starlette application rather than
    replacing it, because `run_http_async` reads `app.state` off what
    `http_app` returned and a bare callable would not have it.
    """
    from fastmcp import FastMCP

    from mars777_police.transport import server

    original_app = FastMCP.http_app

    def http_app(self: Any, *args: Any, **kwargs: Any) -> Any:
        app = original_app(self, *args, **kwargs)
        app.add_middleware(Timed, trace=trace)
        return app

    FastMCP.http_app = http_app  # type: ignore[method-assign]
    server.inbound = timed_async(server.inbound, "tool", "receive_any", trace)
    server.route_receive_turn = timed_router(server.route_receive_turn, trace)


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


STALL_NS = 10_000_000_000
"""Ten seconds: far above a healthy turn, far below the thirty being explained."""


def dispatch_timeline(found: list[dict[str, Any]]) -> str:
    """Say which interval of the ingress holds the long wait, if any does.

    The intervals are read off the last stretch of the trace in order, because
    the request id does not survive below the transport - the tool runs in a
    task the session's receive loop started, not in the one serving the HTTP
    request. Order is sound here only while requests do not overlap, so the
    overlap is reported next to the verdict rather than assumed away.
    """
    ordered = sorted(found, key=lambda one: int(one.get("seq", 0)))
    marks = {
        "asgi_start": "T1 asgi arrival",
        "tool_start": "T2 tool body",
        "router_start": "T3 router",
        "inbound_start": "T4 handler start",
        "inbound_success": "T5 handler success",
        "asgi_end": "T6 asgi end",
    }
    last: dict[str, int] = {}
    for one in ordered:
        event = str(one.get("event"))
        if event in marks:
            last[event] = int(one.get("monotonic_ns", 0))
    lines = ["    dispatch timeline (last observed of each boundary):"]
    for event, label in marks.items():
        lines.append(f"      {label}: {last.get(event, 'absent')}")
    gaps = [
        ("T1->T2 mcp dispatch", "asgi_start", "tool_start"),
        ("T2->T3 tool first await", "tool_start", "router_start"),
        ("T3->T4 router to handler", "router_start", "inbound_start"),
        ("T4->T5 handler body", "inbound_start", "inbound_success"),
        ("T5->T6 response return", "inbound_success", "asgi_end"),
    ]
    widest, widest_name = 0, "none"
    for label, start, end in gaps:
        if start in last and end in last:
            delta = last[end] - last[start]
            lines.append(f"      {label}: {delta / 1e9:.3f}s")
            if delta > widest:
                widest, widest_name = delta, label
        else:
            lines.append(f"      {label}: unmeasured")
    verdict = {
        "T1->T2 mcp dispatch": "A2 - the server application had it; MCP dispatch held it",
        "T2->T3 tool first await": "A3 - the tool body was entered and its first await held it",
        "T3->T4 router to handler": "A3 - the router held it",
        "T4->T5 handler body": "A3 - the handler body held it",
        "T5->T6 response return": "A4 - the handler finished and the response return held it",
    }
    if widest < STALL_NS:
        lines.append("      CLASSIFICATION: A1 - no interval below ASGI holds the wait")
    else:
        lines.append(f"      CLASSIFICATION: {verdict[widest_name]}")
    return "\n".join(lines)


def concurrency(found: list[dict[str, Any]]) -> str:
    """How many ASGI requests were open when the last one arrived."""
    ordered = sorted(found, key=lambda one: int(one.get("seq", 0)))
    starts = [one for one in ordered if one.get("event") == "asgi_start"]
    if not starts:
        return "    asgi requests: none recorded"
    final = starts[-1]
    before = {
        int(one["request_id"])
        for one in ordered
        if one.get("event") == "asgi_start" and int(one.get("seq", 0)) < int(final.get("seq", 0))
    }
    closed = {
        int(one["request_id"])
        for one in ordered
        if one.get("event") in {"asgi_end", "asgi_error"}
        and int(one.get("seq", 0)) < int(final.get("seq", 0))
    }
    return (
        f"    asgi requests: {len(starts)} started;"
        f" still open when the last arrived: {sorted(before - closed)}"
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
        concurrency(found),
        dispatch_timeline(found),
        f"    last {keep} events:",
    ]
    lines.extend(f"      {one}" for one in found[-keep:])
    return "\n".join(lines)
