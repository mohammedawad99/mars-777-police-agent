"""`python -m mars777_police`: launch input, failure paths, and a real process."""

import json
import signal
import subprocess
from collections.abc import Coroutine
from pathlib import Path

import boot_builders as build
import pytest
from r16_source import code_of

from mars777_police import __main__ as entry
from mars777_police.launch_input import (
    LaunchInputError,
    parse_launch_document,
    read_launch_document,
)


def test_the_launch_document_uses_only_frozen_wire_shapes() -> None:
    """`declaration` and `profiles` are the contracts the transport already owns."""
    document = json.loads(build.launch_document())
    assert set(document) == {"declaration", "profiles", "first_sub_game"}
    assert {"game_id", "game_uid", "token_budget_per_series"} <= set(document["declaration"])


def test_the_series_identity_is_derived_not_restated() -> None:
    """Nothing is supplied twice and risked disagreeing."""
    identity = parse_launch_document(build.launch_document())
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
    for name, value in environment(tmp_path).items():
        monkeypatch.setenv(name, value)
    assert entry.main(["--launch", str(tmp_path / "absent.json")]) == 2
    assert "cannot start" in capsys.readouterr().err


def test_missing_settings_exit_non_zero_without_leaking_a_secret(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("MARS777_AUTH_SECRET", raising=False)
    launch = build.written_launch(tmp_path)
    for name, value in environment(tmp_path).items():
        if name != "MARS777_AUTH_SECRET":
            monkeypatch.setenv(name, value)
    assert entry.main(["--launch", str(launch)]) == 2
    reported = capsys.readouterr().err
    assert "MARS777_AUTH_SECRET" in reported
    assert build.SECRET not in reported


def environment(directory: Path, port: int = 0) -> dict[str, str]:
    """A synthetic operator environment; never the real one."""
    return {
        "MARS777_ROLE": entry.ROLE.value,
        "MARS777_BIND_HOST": build.HOST,
        "MARS777_BIND_PORT": str(port or build.free_port()),
        "MARS777_KEY_ID": "mars777-k1",
        "MARS777_AUTH_SECRET": build.SECRET,
        "MARS777_OPPONENT_ENDPOINT": f"http://{build.HOST}:{build.free_port()}/mcp",
    }


def test_the_real_module_serves_and_stops_cleanly(tmp_path: Path) -> None:
    """A real `python -m` process: *answering*, then interrupted, then clean.

    Waiting for FastMCP's own reply rather than a TCP connect is the whole point.
    The listener is bound before the server runs, so an interrupt sent on connect
    can land while `serve` is still starting - before the framework has installed
    its signal handling - and a graceful shutdown becomes a traceback.
    """
    port = build.free_port()
    child = build.spawn(
        "mars777_police", build.written_launch(tmp_path), environment(tmp_path, port)
    )
    try:
        assert build.await_application(child, port) == build.NOT_ACCEPTABLE
        child.send_signal(build.STOP_EVENT)
        out, err = child.communicate(timeout=30)
    finally:
        if child.poll() is None:
            child.kill()
            child.communicate(timeout=10)
    assert child.returncode == 0, err
    assert "Traceback" not in err
    assert build.SECRET not in out and build.SECRET not in err


def test_the_stop_control_and_creation_flag_match_the_platform() -> None:
    """One mapping, chosen by platform - never a police/thief branch."""
    windows = (
        getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", None),
        getattr(signal, "CTRL_BREAK_EVENT", None),
    )
    expected_flag, expected_event = windows if build.WINDOWS else (0, signal.SIGINT)
    assert expected_flag == build.GROUP_FLAG
    assert expected_event == build.STOP_EVENT


def test_windows_can_never_reach_the_unsupported_sigint_path() -> None:
    """`Popen.send_signal(SIGINT)` raises `ValueError` on Windows, so it is unreachable there.

    Read from code tokens, not prose: the control event is selected by the same
    `WINDOWS` test that decides the creation flag, so a group-less child can
    never be sent a group control event either.
    """
    body = code_of(build)
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
