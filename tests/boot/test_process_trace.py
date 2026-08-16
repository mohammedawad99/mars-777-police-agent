"""The opponent-side handler trace, and the reading of it.

Two properties matter and they pull against each other. The wrapper has to be
invisible to the protocol - one call, same arguments, same result, same
exception, no waiting of any kind - because an instrument that changes the
timing of a race is an instrument that can dissolve the thing it was built to
watch. And the reading has to name only the explanation the events can carry,
refusing to choose when they cannot.
"""

import asyncio
import json
from pathlib import Path

import process_trace
import pytest
from boot_builders import SECRET


class Cursor:
    def __init__(self, sub_game: int, step: int) -> None:
        self.sub_game, self.step = sub_game, step


class Message:
    def __init__(self, sub_game: int = 1, step: int = 3) -> None:
        self.cursor = Cursor(sub_game, step)


class Operations:
    """A stand-in for the production inbound operations, counting its calls."""

    def __init__(self) -> None:
        self.calls: list[tuple[object, object]] = []

    def on_acknowledgement(self, message: object, session: object) -> str:
        self.calls.append((message, session))
        return "the original result"

    def on_failing(self, message: object, session: object) -> str:
        self.calls.append((message, session))
        raise LookupError("the original failure")


def _trace(tmp_path: Path) -> process_trace.HandlerTrace:
    return process_trace.HandlerTrace(tmp_path / "trace.jsonl")


def test_a_successful_handler_is_bracketed_by_start_and_success(tmp_path: Path) -> None:
    trace = _trace(tmp_path)
    wrapped = process_trace.traced(
        Operations.on_acknowledgement, process_trace.ACKNOWLEDGEMENT, trace
    )
    operations, message, session = Operations(), Message(1, 7), object()

    assert wrapped(operations, message, session) == "the original result"

    found = process_trace.events(trace.path)
    assert [one["event"] for one in found] == ["inbound_start", "inbound_success"]
    assert all(one["family"] == "acknowledgement" for one in found)
    assert all((one["sub_game"], one["step"]) == (1, 7) for one in found)
    assert [one["seq"] for one in found] == [1, 2]
    assert found[0]["monotonic_ns"] <= found[1]["monotonic_ns"]


def test_a_raising_handler_is_bracketed_by_start_and_error(tmp_path: Path) -> None:
    trace = _trace(tmp_path)
    wrapped = process_trace.traced(Operations.on_failing, process_trace.ACKNOWLEDGEMENT, trace)
    operations = Operations()

    with pytest.raises(LookupError, match="the original failure") as raised:
        wrapped(operations, Message(2, 4), object())

    found = process_trace.events(trace.path)
    assert [one["event"] for one in found] == ["inbound_start", "inbound_error"]
    assert found[1]["error_type"] == "LookupError"
    assert str(raised.value) == "the original failure"


def test_the_original_is_called_exactly_once_with_its_own_arguments(tmp_path: Path) -> None:
    """An instrument that retried, or that swallowed, would change the game."""
    wrapped = process_trace.traced(
        Operations.on_acknowledgement, process_trace.ACKNOWLEDGEMENT, _trace(tmp_path)
    )
    operations, message, session = Operations(), Message(), object()

    wrapped(operations, message, session)

    assert operations.calls == [(message, session)]


def test_installing_wraps_the_three_turn_operations_and_nothing_else(tmp_path: Path) -> None:
    class Target:
        def on_commitment(self, message: object, session: object) -> None: ...

        def on_acknowledgement(self, message: object, session: object) -> None: ...

        def on_reveal(self, message: object, session: object) -> None: ...

        def on_step0(self, message: object, session: object) -> None: ...

    original = Target.on_step0
    process_trace.install(Target, _trace(tmp_path))

    assert Target.on_step0 is original
    for name in process_trace.TRACED:
        assert getattr(Target, name).__name__ == "wrapper"


def test_the_trace_is_parseable_jsonl_and_survives_each_event(tmp_path: Path) -> None:
    """Written a line at a time, because the process in question has been dying."""
    trace = _trace(tmp_path)
    trace.event("inbound_start", process_trace.ACKNOWLEDGEMENT, sub_game=1, step=1)
    on_disk = trace.path.read_text(encoding="utf-8")
    trace.event("inbound_success", process_trace.ACKNOWLEDGEMENT, sub_game=1, step=1)

    assert json.loads(on_disk.strip())["event"] == "inbound_start"
    assert len(trace.path.read_text(encoding="utf-8").strip().splitlines()) == 2


def test_a_half_written_final_line_does_not_lose_the_rest(tmp_path: Path) -> None:
    path = tmp_path / "trace.jsonl"
    path.write_text(
        '{"event": "inbound_start", "family": "acknowledgement", "seq": 1}\n{"ev',
        encoding="utf-8",
    )

    assert [one["seq"] for one in process_trace.events(path)] == [1]


def test_no_trace_file_reads_as_no_events(tmp_path: Path) -> None:
    assert process_trace.events(tmp_path / "absent.jsonl") == []


def _events(*rows: tuple[str, str, int]) -> list[dict[str, object]]:
    return [
        {"event": event, "family": family, "seq": seq, "sub_game": 1, "step": seq}
        for event, family, seq in rows
    ]


def test_no_acknowledgement_at_all_is_the_request_never_arriving() -> None:
    found = _events(("inbound_start", "commitment", 1), ("inbound_success", "commitment", 2))

    assert process_trace.classify(found).startswith("H1")


def test_a_start_without_an_end_is_a_stalled_handler() -> None:
    found = _events(
        ("inbound_start", "acknowledgement", 1),
        ("inbound_success", "acknowledgement", 2),
        ("inbound_start", "acknowledgement", 3),
    )

    assert process_trace.classify(found).startswith("H2")


def test_a_completed_last_acknowledgement_with_nothing_after_is_a_lost_answer() -> None:
    """The real CLI would have revealed next; that reveal is not here."""
    found = _events(
        ("inbound_start", "acknowledgement", 1), ("inbound_success", "acknowledgement", 2)
    )

    assert process_trace.classify(found).startswith("H3")


def test_inbound_work_after_the_last_acknowledgement_means_its_answer_arrived() -> None:
    found = _events(
        ("inbound_start", "acknowledgement", 1),
        ("inbound_success", "acknowledgement", 2),
        ("inbound_start", "reveal", 3),
        ("inbound_success", "reveal", 4),
    )

    assert process_trace.classify(found).startswith("H1")


def test_a_handler_that_raised_is_not_classified() -> None:
    found = _events(
        ("inbound_start", "acknowledgement", 1), ("inbound_error", "acknowledgement", 2)
    )

    assert process_trace.classify(found).startswith("HX")


def test_the_summary_counts_starts_completions_and_the_unmatched(tmp_path: Path) -> None:
    path = tmp_path / "trace.jsonl"
    lines = _events(
        ("inbound_start", "acknowledgement", 1),
        ("inbound_success", "acknowledgement", 2),
        ("inbound_start", "acknowledgement", 3),
    )
    path.write_text("\n".join(json.dumps(one) for one in lines), encoding="utf-8")

    text = process_trace.summary(path)

    assert "acknowledgement starts: 2, completed: 1, unmatched: 1" in text
    assert "CLASSIFICATION: H2" in text


def test_the_trace_records_no_secret(tmp_path: Path) -> None:
    """Only the transmitted cursor and a class name are ever written down."""
    trace = _trace(tmp_path)
    wrapped = process_trace.traced(
        Operations.on_acknowledgement, process_trace.ACKNOWLEDGEMENT, trace
    )

    wrapped(Operations(), Message(), object())

    written = trace.path.read_text(encoding="utf-8")
    assert SECRET not in written
    for forbidden in ("h_commit", "nonce", "secret", "proof", "payload"):
        assert forbidden not in written


class Recorder:
    """A minimal ASGI application that records what it was handed."""

    def __init__(self, status: int = 200) -> None:
        self.calls, self.status, self.received = 0, status, []

    async def __call__(self, scope: object, receive: object, send: object) -> None:
        self.calls += 1
        self.received.append((scope, receive, send))
        await send({"type": "http.response.start", "status": self.status})
        await send({"type": "http.response.body", "body": b"chunk-one", "more_body": True})
        await send({"type": "http.response.body", "body": b"chunk-two"})


async def _drive(app: object, scope: dict[str, object]) -> list[dict[str, object]]:
    sent: list[dict[str, object]] = []

    async def send(message: dict[str, object]) -> None:
        sent.append(message)

    async def receive() -> dict[str, object]:
        return {"type": "http.request"}

    await app(scope, receive, send)
    return sent


def test_the_asgi_wrapper_brackets_a_request_and_forwards_every_message(
    tmp_path: Path,
) -> None:
    """Nothing is buffered: each body chunk goes past untouched, in order."""
    trace = _trace(tmp_path)
    inner = Recorder(status=200)
    wrapped = process_trace.Timed(inner, trace)

    sent = asyncio.run(_drive(wrapped, {"type": "http", "method": "POST", "path": "/mcp"}))

    assert inner.calls == 1
    assert [one["type"] for one in sent] == [
        "http.response.start",
        "http.response.body",
        "http.response.body",
    ]
    assert [one.get("body") for one in sent[1:]] == [b"chunk-one", b"chunk-two"]
    found = process_trace.events(trace.path)
    assert [one["event"] for one in found] == ["asgi_start", "asgi_end"]
    assert found[0]["method"] == "POST" and found[0]["path"] == "/mcp"
    assert found[1]["status"] == 200
    assert found[0]["request_id"] == found[1]["request_id"] == 1


def test_the_asgi_wrapper_passes_a_non_http_scope_straight_through(tmp_path: Path) -> None:
    trace = _trace(tmp_path)
    inner = Recorder()
    wrapped = process_trace.Timed(inner, trace)

    async def run() -> None:
        await wrapped({"type": "lifespan"}, None, _swallow)

    async def _swallow(message: object) -> None:
        return None

    asyncio.run(run())

    assert inner.calls == 1
    assert process_trace.events(trace.path) == []


def test_the_request_id_is_reset_after_each_request(tmp_path: Path) -> None:
    wrapped = process_trace.Timed(Recorder(), _trace(tmp_path))

    asyncio.run(_drive(wrapped, {"type": "http", "method": "POST", "path": "/mcp"}))

    assert process_trace.REQUEST_ID.get() is None


def test_an_asgi_failure_is_recorded_and_re_raised(tmp_path: Path) -> None:
    trace = _trace(tmp_path)

    async def broken(scope: object, receive: object, send: object) -> None:
        raise KeyError("the original asgi failure")

    wrapped = process_trace.Timed(broken, trace)

    with pytest.raises(KeyError):
        asyncio.run(_drive(wrapped, {"type": "http", "method": "POST", "path": "/mcp"}))

    found = process_trace.events(trace.path)
    assert [one["event"] for one in found] == ["asgi_start", "asgi_error"]
    assert found[1]["error_type"] == "KeyError"
    assert process_trace.REQUEST_ID.get() is None


def test_the_awaited_wrapper_is_exact_once_and_transparent(tmp_path: Path) -> None:
    trace = _trace(tmp_path)
    calls = []

    async def original(first: object, second: object = None) -> str:
        calls.append((first, second))
        return "the original result"

    wrapped = process_trace.timed_async(original, "tool", "receive_any", trace)

    assert asyncio.run(wrapped("a", second="b")) == "the original result"
    assert calls == [("a", "b")]
    assert [one["event"] for one in process_trace.events(trace.path)] == [
        "tool_start",
        "tool_success",
    ]


def test_the_awaited_wrapper_preserves_the_original_exception(tmp_path: Path) -> None:
    trace = _trace(tmp_path)
    failure = ValueError("the original await failure")

    async def original() -> None:
        raise failure

    wrapped = process_trace.timed_async(original, "tool", "receive_any", trace)

    with pytest.raises(ValueError) as raised:
        asyncio.run(wrapped())

    assert raised.value is failure
    assert process_trace.events(trace.path)[1]["error_type"] == "ValueError"


def test_the_router_wrapper_is_exact_once_and_names_only_the_kind(tmp_path: Path) -> None:
    trace = _trace(tmp_path)
    calls = []

    def original(operations: object, request: object, session: object) -> str:
        calls.append((operations, request, session))
        return "routed"

    class Request:
        kind = "acknowledgement"

    wrapped = process_trace.timed_router(original, trace)
    request = Request()

    assert wrapped("ops", request, "session") == "routed"
    assert calls == [("ops", request, "session")]
    found = process_trace.events(trace.path)
    assert [one["event"] for one in found] == ["router_start", "router_success"]
    assert all(one["family"] == "acknowledgement" for one in found)


def test_the_router_wrapper_preserves_the_original_exception(tmp_path: Path) -> None:
    trace = _trace(tmp_path)
    failure = TypeError("the original routing failure")

    def original(operations: object, request: object, session: object) -> None:
        raise failure

    class Request:
        kind = "reveal"

    with pytest.raises(TypeError) as raised:
        process_trace.timed_router(original, trace)("ops", Request(), "session")

    assert raised.value is failure
    assert process_trace.events(trace.path)[1]["error_type"] == "TypeError"


def _asgi(
    seq: int, method: str, start: int, end: int | None = None, status: int | None = 200
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = [
        {
            "event": "asgi_start",
            "family": "http",
            "layer": "asgi",
            "seq": seq * 2 - 1,
            "request_id": seq,
            "method": method,
            "path": "/mcp",
            "monotonic_ns": start,
        }
    ]
    if end is not None:
        rows.append(
            {
                "event": "asgi_end",
                "family": "http",
                "layer": "asgi",
                "seq": seq * 2,
                "request_id": seq,
                "method": method,
                "path": "/mcp",
                "monotonic_ns": end,
                "status": status,
            }
        )
    return rows


def test_the_ledger_keeps_a_request_that_never_finished() -> None:
    """The interesting request is the one still open; it must not be dropped."""
    found = [*_asgi(1, "POST", 0, 1_000_000), *_asgi(2, "POST", 2_000_000)]

    rows = process_trace.ledger(found)

    assert rows[2]["end_ns"] is None
    assert rows[2]["method"] == "POST"
    assert rows[1]["end_ns"] == 1_000_000


def test_later_requests_do_not_overwrite_an_earlier_open_one() -> None:
    """R6 lost requests 72 and 73 to a twelve-event window; the ledger cannot."""
    found = [
        *_asgi(72, "POST", 1_000_000_000, 32_000_000_000),
        *_asgi(73, "GET", 1_500_000_000, 32_000_000_000),
        *_asgi(74, "DELETE", 31_900_000_000, 31_950_000_000),
    ]

    rows = process_trace.ledger(found)

    assert sorted(rows) == [72, 73, 74]
    assert rows[72]["method"] == "POST" and rows[73]["method"] == "GET"
    text = process_trace.stall_report(found)
    assert "# 72 POST" in text and "# 73 GET" in text


def test_exactly_one_long_held_post_is_the_discriminator() -> None:
    found = [
        *_asgi(1, "POST", 0, 100_000_000),
        *_asgi(2, "GET", 0, 31_000_000_000),
        *_asgi(3, "POST", 500_000_000, 31_000_000_000),
    ]

    assert process_trace.stall_verdict(process_trace.ledger(found)).startswith("A2")


def test_no_long_held_post_is_delivery_below_asgi() -> None:
    found = [*_asgi(1, "POST", 0, 100_000_000), *_asgi(2, "GET", 0, 31_000_000_000)]

    assert process_trace.stall_verdict(process_trace.ledger(found)).startswith("A1")


def test_two_long_held_posts_are_ambiguous_not_a_stronger_result() -> None:
    found = [
        *_asgi(1, "POST", 0, 31_000_000_000),
        *_asgi(2, "POST", 100_000_000, 31_500_000_000),
    ]

    assert process_trace.stall_verdict(process_trace.ledger(found)).startswith("AX")


def test_open_across_names_only_what_spanned_the_moment() -> None:
    found = [
        *_asgi(1, "POST", 0, 1_000),
        *_asgi(2, "POST", 500, 5_000),
        *_asgi(3, "GET", 900),
    ]

    assert sorted(one["seq"] for one in process_trace.open_across(found, 2_000)) == [2, 3]


def test_the_teardown_marker_is_reported_and_closes_nothing() -> None:
    found = [
        *_asgi(1, "POST", 0, 31_000_000_000),
        {
            "event": "teardown_start",
            "family": "lifecycle",
            "layer": "asgi",
            "seq": 99,
            "monotonic_ns": 30_000_000_000,
        },
    ]

    text = process_trace.stall_report(found)

    assert "teardown_start: 30.000s after baseline" in text
    assert process_trace.ledger(found)[1]["end_ns"] == 31_000_000_000


def test_router_events_do_not_contaminate_handler_counts(tmp_path: Path) -> None:
    """R6 counted twenty-two starts against sixty-six completions this way."""
    path = tmp_path / "trace.jsonl"
    rows = [
        {
            "event": "inbound_start",
            "family": "acknowledgement",
            "layer": "handler",
            "seq": 1,
            "monotonic_ns": 0,
            "sub_game": 1,
            "step": 1,
        },
        {
            "event": "inbound_success",
            "family": "acknowledgement",
            "layer": "handler",
            "seq": 2,
            "monotonic_ns": 1,
            "sub_game": 1,
            "step": 1,
        },
        {
            "event": "router_start",
            "family": "acknowledgement",
            "layer": "router",
            "seq": 3,
            "monotonic_ns": 2,
        },
        {
            "event": "router_success",
            "family": "acknowledgement",
            "layer": "router",
            "seq": 4,
            "monotonic_ns": 3,
        },
    ]
    path.write_text("\n".join(json.dumps(one) for one in rows), encoding="utf-8")

    text = process_trace.summary(path)

    assert "acknowledgement starts: 1, completed: 1, unmatched: 0" in text


def test_asgi_events_do_not_change_the_handler_classification() -> None:
    """An `asgi_end` is not inbound application work, whatever its sequence."""
    handled = [
        {"event": "inbound_start", "family": "acknowledgement", "layer": "handler", "seq": 1},
        {"event": "inbound_success", "family": "acknowledgement", "layer": "handler", "seq": 2},
    ]

    assert process_trace.classify(handled).startswith("H3")
    assert process_trace.classify(
        [*handled, {"event": "asgi_end", "family": "http", "layer": "asgi", "seq": 3}]
    ).startswith("H3")
