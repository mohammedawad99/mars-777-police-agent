"""The opponent-side handler trace, and the reading of it.

Two properties matter and they pull against each other. The wrapper has to be
invisible to the protocol - one call, same arguments, same result, same
exception, no waiting of any kind - because an instrument that changes the
timing of a race is an instrument that can dissolve the thing it was built to
watch. And the reading has to name only the explanation the events can carry,
refusing to choose when they cannot.
"""

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
