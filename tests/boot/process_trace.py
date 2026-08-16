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

ASGI, TOOL, ROUTER, HANDLER = "asgi", "tool", "router", "handler"
"""The instrumentation depths, kept apart from what a message *means*."""

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

    def event(self, event: str, family: str, layer: str = HANDLER, **fields: object) -> None:
        """Write one boundary, naming the layer it came from as well as the family.

        The layer is separate from the family on purpose. R6 recorded the
        router's events under `family="acknowledgement"` too, so counting
        acknowledgement handlers counted three layers at once and reported
        twenty-two starts against sixty-six completions. Instrumentation depth
        and protocol meaning are different questions and now have different
        fields.
        """
        self.sequence += 1
        record: dict[str, object] = {
            "event": event,
            "family": family,
            "layer": layer,
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
        trace.event("inbound_start", family, layer=HANDLER, **where)
        try:
            result = original(operations, message, session)
        except BaseException as failure:
            trace.event(
                "inbound_error", family, layer=HANDLER, error_type=type(failure).__name__, **where
            )
            raise
        trace.event("inbound_success", family, layer=HANDLER, **where)
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

        async def listened() -> Any:
            """Time the receive channel, and hand back exactly what it gave.

            The body is never read here - only how many bytes a chunk carried
            and whether more were promised, which is what separates "no first
            byte yet" from "body arriving in pieces".
            """
            self.trace.event("receive_wait", "http", layer=ASGI, request_id=request_id)
            message = await receive()
            body = message.get("body")
            self.trace.event(
                "receive_return",
                "http",
                layer=ASGI,
                request_id=request_id,
                message_type=message.get("type"),
                body_len=len(body) if isinstance(body, bytes | bytearray) else None,
                more_body=message.get("more_body"),
            )
            return message

        self.trace.event(
            "asgi_start",
            "http",
            layer=ASGI,
            request_id=request_id,
            method=scope.get("method"),
            path=scope.get("path"),
        )
        token = REQUEST_ID.set(request_id)
        try:
            await self.app(scope, listened, watched)
        except BaseException as failure:
            self.trace.event(
                "asgi_error",
                "http",
                layer=ASGI,
                request_id=request_id,
                error_type=type(failure).__name__,
            )
            raise
        else:
            self.trace.event(
                "asgi_end",
                "http",
                layer=ASGI,
                request_id=request_id,
                method=scope.get("method"),
                path=scope.get("path"),
                status=seen[0] if seen else None,
            )
        finally:
            REQUEST_ID.reset(token)


def timed_async(
    original: Callable[..., Awaitable[Any]], event: str, family: str, trace: HandlerTrace
) -> Callable[..., Awaitable[Any]]:
    """Bracket one awaited callable, carrying whatever request id is in scope."""

    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        trace.event(f"{event}_start", family, layer=TOOL, request_id=REQUEST_ID.get())
        try:
            result = await original(*args, **kwargs)
        except BaseException as failure:
            trace.event(
                f"{event}_error",
                family,
                layer=TOOL,
                request_id=REQUEST_ID.get(),
                error_type=type(failure).__name__,
            )
            raise
        trace.event(f"{event}_success", family, layer=TOOL, request_id=REQUEST_ID.get())
        return result

    return wrapper


def timed_router(original: Callable[..., Any], trace: HandlerTrace) -> Callable[..., Any]:
    """Bracket the turn router, naming only the request kind it dispatches on."""

    def wrapper(operations: Any, request: Any, session: Any) -> Any:
        kind = getattr(request, "kind", None)
        trace.event("router_start", str(kind), layer=ROUTER, request_id=REQUEST_ID.get())
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
        trace.event("router_success", str(kind), layer=ROUTER, request_id=REQUEST_ID.get())
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

    from mars777_police.agent_runtime import AgentRuntime
    from mars777_police.transport import server

    original_app = FastMCP.http_app

    def http_app(self: Any, *args: Any, **kwargs: Any) -> Any:
        app = original_app(self, *args, **kwargs)
        app.add_middleware(Timed, trace=trace)
        return app

    FastMCP.http_app = http_app  # type: ignore[method-assign]
    server.inbound = timed_async(server.inbound, "tool", "receive_any", trace)
    server.route_receive_turn = timed_router(server.route_receive_turn, trace)

    original_stop = AgentRuntime.stop

    async def stop(self: Any) -> Any:
        """Mark the terminal boundary immediately before the real stop runs."""
        trace.event("teardown_start", "lifecycle", layer=ASGI)
        return await original_stop(self)

    AgentRuntime.stop = stop  # type: ignore[method-assign]


SESSION = "session"
"""The MCP layer below our tool: transport, session loop and lowlevel dispatch."""


def timed_library(
    original: Callable[..., Awaitable[Any]], event: str, trace: HandlerTrace, describe: Any = None
) -> Callable[..., Awaitable[Any]]:
    """Bracket one installed MCP coroutine without changing anything it does.

    Called exactly once with exactly its own arguments; its result and its
    exception both leave unchanged. No buffer, timeout, lock or task is created
    here, so the stream capacities and the cancellation behaviour under test
    remain the ones the library ships.
    """

    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        about = {} if describe is None else describe(*args, **kwargs)
        trace.event(f"{event}_enter", "mcp", layer=SESSION, **about)
        try:
            result = await original(*args, **kwargs)
        except BaseException as failure:
            trace.event(
                f"{event}_error",
                "mcp",
                layer=SESSION,
                error_type=type(failure).__name__,
                **about,
            )
            raise
        trace.event(f"{event}_exit", "mcp", layer=SESSION, **about)
        return result

    return wrapper


def _post_about(_self: Any, scope: Any = None, *_rest: Any, **_kw: Any) -> dict[str, Any]:
    """Only the method and path: the body is never read for a diagnostic."""
    return {"method": (scope or {}).get("method"), "path": (scope or {}).get("path")}


def _message_about(_self: Any, message: Any = None, *_rest: Any, **_kw: Any) -> dict[str, Any]:
    """The message's own class name, and a tool name when it already decoded one."""
    request = getattr(getattr(message, "request", None), "root", None)
    return {
        "message_type": type(message).__name__,
        "request_type": type(request).__name__ if request is not None else None,
        "tool": getattr(getattr(request, "params", None), "name", None),
    }


def install_session(trace: HandlerTrace) -> None:
    """Time the MCP session path the ledger narrowed the delay down to.

    Four boundaries, each a coroutine the installed packages define: the POST
    handler, the session's hand-off of a decoded request, and the lowlevel
    dispatch that starts a tool task. Between them they say whether the first
    zero-buffer send is what waits, or whether the single receive loop is held
    by the message before it.
    """
    from mcp.server.lowlevel.server import Server
    from mcp.server.session import ServerSession
    from mcp.server.streamable_http import StreamableHTTPServerTransport

    StreamableHTTPServerTransport._handle_post_request = timed_library(  # type: ignore[method-assign]
        StreamableHTTPServerTransport._handle_post_request, "post", trace, _post_about
    )
    ServerSession._handle_incoming = timed_library(  # type: ignore[method-assign]
        ServerSession._handle_incoming, "handoff", trace, _message_about
    )
    Server._handle_message = timed_library(  # type: ignore[method-assign]
        Server._handle_message, "dispatch", trace, _message_about
    )


CLIENT = "client"
"""The sending side: httpcore's HTTP/1.1 header and body writes."""


def _request_about(connection: Any, request: Any = None, **_kw: Any) -> dict[str, Any]:
    """Method, target, declared length and which connection carried it.

    `Content-Length` is a number, not content, and the connection is named by
    local object identity so reuse is visible. No other header is read and the
    body is never touched - iterating it here would consume the request.
    """
    length = None
    for name, value in getattr(request, "headers", None) or []:
        if bytes(name).lower() == b"content-length":
            length = int(bytes(value))
    target = getattr(getattr(request, "url", None), "target", None)
    method = getattr(request, "method", None)
    return {
        "method": bytes(method).decode() if method is not None else None,
        "path": bytes(target).decode() if target is not None else None,
        "content_length": length,
        "connection": id(connection),
    }


def install_client(trace: HandlerTrace) -> None:
    """Time the real CLI's own HTTP writes, in that process only.

    The two calls wrapped are where httpcore hands header and body bytes to
    the network stream, which is the only place that can say whether this side
    put the request on the wire promptly. A high-level hook would fire before
    any byte was written and would prove nothing.
    """
    from httpcore._async.http11 import AsyncHTTP11Connection

    AsyncHTTP11Connection._send_request_headers = timed_library(  # type: ignore[method-assign]
        AsyncHTTP11Connection._send_request_headers, "client_headers", trace, _request_about
    )
    AsyncHTTP11Connection._send_request_body = timed_library(  # type: ignore[method-assign]
        AsyncHTTP11Connection._send_request_body, "client_body", trace, _request_about
    )


def client_report(path: Path, keep: int = 12) -> str:
    """When the sending side actually wrote each request, and for how long."""
    found = events(path)
    writes = [one for one in found if str(one.get("event")).startswith("client_")]
    if not writes:
        return "    client write trace: no events recorded"
    base = min(int(one.get("monotonic_ns", 0)) for one in writes)
    lines = [f"    client write trace: {len(writes)} events, baseline={base}"]
    slowest, slowest_at = 0, None
    opened: dict[str, dict[str, Any]] = {}
    for one in sorted(writes, key=lambda item: int(item.get("seq", 0))):
        name, _, phase = str(one.get("event")).rpartition("_")
        if phase == "enter":
            opened[name] = one
        elif name in opened:
            started = opened.pop(name)
            held = int(one.get("monotonic_ns", 0)) - int(started["monotonic_ns"])
            if held > slowest:
                slowest, slowest_at = held, started
    body = [one for one in writes if str(one.get("event")).startswith("client_body")]
    lines.append(
        f"      body writes: {len([one for one in body if one['event'].endswith('enter')])}"
    )
    lines.append(f"      slowest single write: {slowest / 1e9:.3f}s {_about(slowest_at or {})}")
    lines.append(f"      last {keep} client events:")
    for one in sorted(writes, key=lambda item: int(item.get("seq", 0)))[-keep:]:
        when = (int(one.get("monotonic_ns", 0)) - base) / 1e9
        lines.append(f"        {when:9.3f}s {one.get('event')} {_about(one)}")
    return "\n".join(lines)


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
    inbound = [one for one in found if one.get("layer", HANDLER) == HANDLER]
    acknowledgements = [one for one in inbound if one.get("family") == ACKNOWLEDGEMENT]
    if not acknowledgements:
        return "H1 - no acknowledgement ever reached the instrumented handler"
    last = acknowledgements[-1]
    if last.get("event") == "inbound_start":
        return "H2 - the last acknowledgement handler began and never returned"
    if last.get("event") == "inbound_error":
        return "HX - the last acknowledgement handler raised; a caller should have seen that"
    after = [one for one in inbound if int(one.get("seq", 0)) > int(last.get("seq", 0))]
    if not after:
        return "H3 - the last acknowledgement completed and nothing inbound followed it"
    return (
        "H1 - the last acknowledgement completed and inbound work followed it,"
        " so the one finally awaited never reached a handler"
    )


STALL_NS = 10_000_000_000
"""Ten seconds: far above a healthy turn, far below the thirty being explained."""


def ledger(found: list[dict[str, Any]]) -> dict[int, dict[str, Any]]:
    """Every ASGI request this process served, whether or not it ever finished.

    Kept as a ledger rather than a tail, because R6 printed only the last
    twelve events and the two requests that mattered - the ones open across
    the stall - had started long before that window. A request that never ends
    is the interesting kind here, so an absent end is recorded as `None` and
    never as a closed row.
    """
    rows: dict[int, dict[str, Any]] = {}
    for one in sorted(found, key=lambda item: int(item.get("seq", 0))):
        if one.get("layer") != ASGI:
            continue
        request_id = int(one.get("request_id", 0))
        if one.get("event") == "asgi_start":
            rows[request_id] = {
                "seq": request_id,
                "method": one.get("method"),
                "path": one.get("path"),
                "start_ns": int(one.get("monotonic_ns", 0)),
                "end_ns": None,
                "status": None,
                "error_type": None,
            }
        elif request_id in rows:
            rows[request_id]["end_ns"] = int(one.get("monotonic_ns", 0))
            rows[request_id]["status"] = one.get("status")
            rows[request_id]["error_type"] = one.get("error_type")
    return rows


def _row(one: dict[str, Any], base: int) -> str:
    end = one["end_ns"]
    held = "open" if end is None else f"{(end - one['start_ns']) / 1e9:.3f}s"
    ended = "never" if end is None else f"{(end - base) / 1e9:.3f}s"
    return (
        f"      #{one['seq']:>3} {one['method']!s:<6} {one['path']!s:<6}"
        f" start={(one['start_ns'] - base) / 1e9:8.3f}s end={ended:>10} held={held:>9}"
        f" status={one['status']} error={one['error_type']}"
    )


def open_across(found: list[dict[str, Any]], at_ns: int) -> list[dict[str, Any]]:
    """The requests that had started before *at_ns* and had not finished by it."""
    return [
        one
        for one in ledger(found).values()
        if one["start_ns"] <= at_ns and (one["end_ns"] is None or one["end_ns"] > at_ns)
    ]


def stall_report(found: list[dict[str, Any]], keep: int = 10) -> str:
    """The ledger view that decides A1 from A2, and the reasoning behind it.

    The decisive question is whether a POST was already inside this server for
    the whole thirty seconds. That is answered by one request's own start and
    end, so those are printed in full rather than inferred from a global last
    of each boundary - the mistake that made R6's verdict meaningless.
    """
    rows = ledger(found)
    if not rows:
        return "    asgi ledger: no requests recorded"
    base = min(one["start_ns"] for one in rows.values())
    handlers = [
        one
        for one in found
        if one.get("layer", HANDLER) == HANDLER and one.get("event") == "inbound_start"
    ]
    last_handler = handlers[-1] if handlers else None
    teardown = [one for one in found if one.get("event") == "teardown_start"]
    at = (
        int(teardown[0]["monotonic_ns"])
        if teardown
        else max((one["end_ns"] or one["start_ns"] for one in rows.values()), default=base)
    )
    marker = (
        "absent"
        if not teardown
        else f"{(int(teardown[0]['monotonic_ns']) - base) / 1e9:.3f}s after baseline"
    )
    lines = [
        f"    asgi ledger: {len(rows)} requests, baseline={base}",
        f"    teardown_start: {marker}",
    ]
    if last_handler is not None:
        lines.append(
            f"    last handler dispatch: {last_handler.get('family')}"
            f" sub_game={last_handler.get('sub_game')} step={last_handler.get('step')}"
            f" at {(int(last_handler['monotonic_ns']) - base) / 1e9:.3f}s"
        )
    lines.append(f"    last {keep} requests:")
    lines.extend(_row(one, base) for one in sorted(rows.values(), key=lambda r: r["seq"])[-keep:])
    still = sorted(open_across(found, at), key=lambda r: r["seq"])
    lines.append(f"    open at the terminal boundary ({len(still)}):")
    lines.extend(_row(one, base) for one in still)
    held = [one for one in rows.values() if one["method"] == "POST" and _held(one) >= STALL_NS]
    lines.append(f"    POSTs held >= 10s ({len(held)}):")
    lines.extend(_row(one, base) for one in sorted(held, key=lambda r: r["seq"]))
    lines.append(f"    CLASSIFICATION: {stall_verdict(rows)}")
    lines.append(session_report(found, base))
    return "\n".join(lines)


def session_report(found: list[dict[str, Any]], base: int) -> str:
    """Where the MCP session path spent the wait, and which await owned it.

    Two shapes are distinguishable. A hand-off that itself takes the whole wait
    means the single receive loop was held by the message before ours. A gap
    between one hand-off finishing and the next beginning means the loop was
    idle and the POST had not yet been given to it, which puts the wait on the
    first zero-buffer send instead.
    """
    session = [one for one in found if one.get("layer") == SESSION]
    if not session:
        return "    mcp session path: not instrumented in this run"
    ordered = sorted(session, key=lambda one: int(one.get("seq", 0)))
    lines = ["    mcp session path:"]
    slowest, slowest_at = 0, None
    opened: dict[str, dict[str, Any]] = {}
    for one in ordered:
        event = str(one.get("event"))
        name, _, phase = event.rpartition("_")
        if phase == "enter":
            opened[name] = one
        elif name in opened:
            held = int(one.get("monotonic_ns", 0)) - int(opened[name]["monotonic_ns"])
            if held > slowest:
                slowest, slowest_at = held, (name, opened.pop(name, one), one)
            else:
                opened.pop(name, None)
    gap, gap_at = 0, None
    handoffs = [one for one in ordered if str(one.get("event")).startswith("handoff_")]
    for earlier, later in itertools.pairwise(handoffs):
        if (
            str(earlier.get("event")) == "handoff_exit"
            and str(later.get("event")) == "handoff_enter"
        ):
            between = int(later.get("monotonic_ns", 0)) - int(earlier.get("monotonic_ns", 0))
            if between > gap:
                gap, gap_at = between, (earlier, later)
    lines.append(f"    session events: {len(session)}")
    if slowest_at is not None:
        name, started, ended = slowest_at
        lines.append(
            f"      slowest {name}: {slowest / 1e9:.3f}s"
            f" start={(int(started['monotonic_ns']) - base) / 1e9:.3f}s"
            f" end={(int(ended['monotonic_ns']) - base) / 1e9:.3f}s {_about(started)}"
        )
    if gap_at is not None:
        earlier, later = gap_at
        lines.append(
            f"      widest idle gap between hand-offs: {gap / 1e9:.3f}s"
            f" after={(int(earlier['monotonic_ns']) - base) / 1e9:.3f}s"
            f" next={(int(later['monotonic_ns']) - base) / 1e9:.3f}s {_about(later)}"
        )
    lines.append(f"      BLOCKER: {blocker_verdict(slowest, slowest_at, gap)}")
    return "\n".join(lines)


def _about(one: dict[str, Any]) -> str:
    keys = (
        "method",
        "path",
        "message_type",
        "request_type",
        "tool",
        "content_length",
        "connection",
        "body_len",
        "more_body",
    )
    return " ".join(f"{key}={one[key]}" for key in keys if one.get(key) is not None)


def blocker_verdict(slowest: int, slowest_at: Any, gap: int) -> str:
    """Name the owning await only when one of the two shapes clearly dominates."""
    if slowest < STALL_NS and gap < STALL_NS:
        return "BX - no session-path await or gap held the wait"
    if slowest_at is not None and slowest >= STALL_NS and slowest >= gap:
        name = slowest_at[0]
        if name == "handoff":
            return "B3 - the session hand-off of the previous message held the receive loop"
        if name == "dispatch":
            return "B4 - lowlevel dispatch of the previous message held it"
        return "B1 - the POST handler itself held it, before the receive loop saw it"
    return "B1 - the receive loop was idle; the POST had not yet crossed the first send"


def _held(one: dict[str, Any]) -> int:
    """How long a request was inside this server, counting an open one to the end."""
    if one["end_ns"] is None:
        return STALL_NS * 1000
    return int(one["end_ns"]) - int(one["start_ns"])


def stall_verdict(rows: dict[int, dict[str, Any]]) -> str:
    """A1, A2 or AX, decided only by how many POSTs were held long enough.

    Exactly one long-held POST is the discriminator: it entered this server
    promptly and stayed inside it across the wait, which places the delay above
    the tool and below ASGI arrival. More than one candidate is ambiguity, not
    a stronger result, and is reported as such.
    """
    held = [one for one in rows.values() if one["method"] == "POST" and _held(one) >= STALL_NS]
    if not held:
        return "A1 - no POST was inside this server across the stall"
    if len(held) > 1:
        return f"AX - {len(held)} POSTs were held that long; identity is not unique"
    return "A2 - exactly one POST was inside this server across the stall"


def summary(path: Path, keep: int = 12) -> str:
    """The tail of the trace, what it implies, and the numbers behind it."""
    found = events(path)
    inbound = [one for one in found if one.get("layer", HANDLER) == HANDLER]
    acknowledgements = [one for one in inbound if one.get("family") == ACKNOWLEDGEMENT]
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
        stall_report(found),
        f"    last {keep} events:",
    ]
    lines.extend(f"      {one}" for one in found[-keep:])
    return "\n".join(lines)
