"""`python -m mars777_police`: launch input, failure paths, and a real process."""

import json
import signal
import subprocess
from collections.abc import Coroutine
from pathlib import Path

import executable_evidence as evidence
import executable_outcome as outcome
import executable_process as process
import pytest
from boot_builders import SECRET, free_port
from r16_source import code_of

from mars777_police import __main__ as entry
from mars777_police.launch_input import (
    LaunchInputError,
    parse_launch_document,
    read_launch_document,
)


def test_the_launch_document_uses_only_frozen_wire_shapes() -> None:
    """`declaration`, `profiles` and `config` are contracts the transport owns."""
    document = json.loads(process.launch_document())
    assert set(document) == {"declaration", "profiles", "config", "first_sub_game"}
    assert {"game_id", "game_uid", "token_budget_per_series"} <= set(document["declaration"])


def test_the_series_identity_is_derived_not_restated() -> None:
    """Nothing is supplied twice and risked disagreeing."""
    identity = parse_launch_document(process.launch_document()).identity
    assert identity.game_id == identity.declaration.game_id
    assert identity.game_uid == identity.declaration.game_uid
    assert identity.token_budget_per_series == identity.declaration.token_budget_per_series


@pytest.mark.parametrize("broken", ["", "   ", "not json", '{"first_sub_game": 1}'])
def test_a_malformed_launch_document_is_refused(broken: str, tmp_path: Path) -> None:
    path = tmp_path / "launch.json"
    path.write_text(broken, encoding="utf-8")
    with pytest.raises(LaunchInputError):
        read_launch_document(path)


def test_a_missing_launch_document_is_refused(tmp_path: Path) -> None:
    with pytest.raises(LaunchInputError, match="could not be read"):
        read_launch_document(tmp_path / "absent.json")


def test_help_starts_nothing(capsys: pytest.CaptureFixture[str]) -> None:
    """`--help` needs no settings, no network and no secret."""
    with pytest.raises(SystemExit) as raised:
        entry.parse_args(["--help"])
    assert raised.value.code == 0
    assert "--launch" in capsys.readouterr().out


def test_a_bad_launch_path_exits_non_zero_without_starting(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    for name, value in process.environment().items():
        monkeypatch.setenv(name, value)
    assert entry.main(["--launch", str(tmp_path / "absent.json")]) == 2
    assert "cannot start" in capsys.readouterr().err


def test_missing_settings_exit_non_zero_without_leaking_a_secret(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("MARS777_AUTH_SECRET", raising=False)
    launch = process.written_launch(tmp_path)
    for name, value in process.environment().items():
        if name != "MARS777_AUTH_SECRET":
            monkeypatch.setenv(name, value)
    assert entry.main(["--launch", str(launch)]) == 2
    reported = capsys.readouterr().err
    assert "MARS777_AUTH_SECRET" in reported
    assert SECRET not in reported


def test_the_real_module_serves_and_stops_cleanly(tmp_path: Path) -> None:
    """A real `python -m` process: *answering*, then interrupted, then clean.

    Waiting for FastMCP's own reply rather than a TCP connect is the point: the
    listener is bound before the server runs, so an interrupt sent on connect can
    land before the framework installs its signal handling.
    """
    port, launch = free_port(), process.written_launch(tmp_path)
    child = process.spawn("mars777_police", launch, process.environment(port))
    try:
        assert outcome.await_application(child, port) == process.NOT_ACCEPTABLE
        child.send_signal(process.STOP_EVENT)
        out, err = child.communicate(timeout=30)
    finally:
        if child.poll() is None:
            child.kill()
            child.communicate(timeout=10)
    evidence.assert_clean_operator_stop(child.returncode, out, err)


GRACEFUL = "\n".join(process.GRACEFUL_MARKERS)
CONTRACT = [
    (0, GRACEFUL, True, True),
    (process.CONTROL_EXIT, GRACEFUL, True, True),
    (process.CONTROL_EXIT, "Shutting down\nApplication shutdown complete", True, False),
    (process.CONTROL_EXIT, f"{GRACEFUL}\nTraceback (most recent call last):", True, False),
    (2, GRACEFUL, True, False),
    (process.CONTROL_EXIT, GRACEFUL, False, False),
]


@pytest.mark.parametrize(("status", "err", "windows", "clean"), CONTRACT)
def test_the_clean_operator_stop_contract_is_platform_exact(
    status: int, err: str, windows: bool, clean: bool
) -> None:
    """Windows may report 3 after a control event; that alone is never success."""
    if clean:
        evidence.assert_clean_operator_stop(status, "", err, windows=windows)
        return
    with pytest.raises(AssertionError):
        evidence.assert_clean_operator_stop(status, "", err, windows=windows)


def test_the_platform_stop_mapping_is_exact_and_never_sigint_on_windows() -> None:
    """One `WINDOWS` test picks both the creation flag and the control event, and
    `Popen.send_signal(SIGINT)` - which raises there - stays unreachable."""
    windows = (
        getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", None),
        getattr(signal, "CTRL_BREAK_EVENT", None),
    )
    expected_flag, expected_event = windows if process.WINDOWS else (0, signal.SIGINT)
    assert expected_flag == process.GROUP_FLAG
    assert expected_event == process.STOP_EVENT
    body = code_of(process)
    assert "signal . CTRL_BREAK_EVENT if WINDOWS else signal . SIGINT" in body
    assert "subprocess . CREATE_NEW_PROCESS_GROUP if WINDOWS else 0" in body
    assert "send_signal" not in body


def test_an_interrupt_during_the_run_exits_zero(monkeypatch: pytest.MonkeyPatch) -> None:
    """The portable fallback path, where a signal escapes as KeyboardInterrupt."""

    def interrupted(coro: Coroutine[object, object, None]) -> None:
        coro.close()
        raise KeyboardInterrupt

    monkeypatch.setattr(entry.asyncio, "run", interrupted)
    assert entry.main(["--launch", "unused.json"]) == 0


def test_a_peer_protocol_refusal_exits_with_its_own_identity(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """A refusal from a peer that is really there is reported, never retried."""
    from mars777_police.app.protocol_errors import ConfigMismatchError

    def refuse(coro: Coroutine[object, object, object]) -> None:
        coro.close()
        raise ConfigMismatchError(ConfigMismatchError.error_id)

    monkeypatch.setattr(entry.asyncio, "run", refuse)
    assert entry.main(["--launch", "unused.json"]) == 5
    assert "E-CONFIG-MISMATCH" in capsys.readouterr().err


def test_a_local_defect_keeps_its_traceback(monkeypatch: pytest.MonkeyPatch) -> None:
    """A bug is not translated into "the peer was unreachable"."""
    from mars777_police.app.protocol_errors import LocalDefectError

    def defect(coro: Coroutine[object, object, object]) -> None:
        coro.close()
        raise LocalDefectError("a defect")

    monkeypatch.setattr(entry.asyncio, "run", defect)
    with pytest.raises(LocalDefectError):
        entry.main(["--launch", "unused.json"])
