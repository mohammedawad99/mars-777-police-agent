"""The command a grader runs, and the status it leaves behind."""

from pathlib import Path

import pytest
import replay_fixtures as fixtures

from mars777_police import replay_main

OTHER = "f" * 64


def argv(tmp_path: Path, *extra: str) -> list[str]:
    log, config = fixtures.played(tmp_path)
    return ["--log", str(log), "--config", str(config), *extra]


def test_a_clean_replay_is_status_zero(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    command = argv(tmp_path, "--summary")
    capsys.readouterr()

    status = replay_main.main(command)
    printed = capsys.readouterr().out

    assert status == 0
    assert "Verified OK" in printed
    assert "CONSISTENT" in printed


def test_a_turn_without_a_hint_prints_no_hint_line(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    command = argv(tmp_path)
    log = Path(command[1])
    document = fixtures.document(log)
    document["entries"] = [one for one in document["entries"] if one["phase"] != "reveal"]
    fixtures.rewritten(log, document)
    capsys.readouterr()

    replay_main.main(command)

    assert "hint:" not in capsys.readouterr().out


def test_the_full_view_prints_a_board_per_step(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    command = argv(tmp_path)
    capsys.readouterr()

    replay_main.main(command)
    printed = capsys.readouterr().out

    assert "-- step 1 --" in printed and "-- step 2 --" in printed
    assert "police" in printed and "barrier" in printed


def test_one_step_can_be_asked_for(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    command = argv(tmp_path, "--step", "2")
    capsys.readouterr()

    replay_main.main(command)
    printed = capsys.readouterr().out

    assert "-- step 2 --" in printed
    assert "-- step 1 --" not in printed


def test_a_step_that_does_not_exist_is_a_refusal(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    command = argv(tmp_path, "--step", "9")
    capsys.readouterr()

    status = replay_main.main(command)

    assert status == 2
    assert "cannot replay" in capsys.readouterr().err


def test_a_tampered_log_is_status_three(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """The tool ran; what it found is the non-zero part."""
    command = argv(tmp_path, "--summary")
    log = Path(command[1])
    document = fixtures.document(log)
    for entry in document["entries"]:  # type: ignore[union-attr]
        if entry["phase"] == "commit":
            entry["commit"] = OTHER
            break
    fixtures.rewritten(log, document)
    capsys.readouterr()

    status = replay_main.main(command)

    assert status == 3
    assert "TAMPERED" in capsys.readouterr().out


def test_a_missing_file_is_status_two_and_no_traceback(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _, config = fixtures.played(tmp_path)
    capsys.readouterr()  # the fixture played a real sub-game; that noise is not ours

    status = replay_main.main(["--log", str(tmp_path / "absent.json"), "--config", str(config)])
    captured = capsys.readouterr()

    assert status == 2
    assert captured.err.startswith("cannot replay:")
    assert "Traceback" not in captured.err


def test_an_evidence_root_confines_the_paths(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    command = argv(tmp_path, "--summary", "--root", str(tmp_path / "police"))

    assert replay_main.main(command) == 0


def test_a_path_outside_the_root_is_refused(tmp_path: Path) -> None:
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    command = argv(tmp_path, "--summary", "--root", str(elsewhere))

    assert replay_main.main(command) == 2


def test_the_command_needs_both_files() -> None:
    with pytest.raises(SystemExit):
        replay_main.parse_args(["--log", "only.json"])


def test_the_viewer_is_runnable_as_a_module(tmp_path: Path) -> None:
    """`uv run python -m …replay_main` really is the entry point."""
    import subprocess
    import sys

    log, config = fixtures.played(tmp_path)
    finished = subprocess.run(
        [
            sys.executable,
            "-m",
            "mars777_police.replay_main",
            "--log",
            str(log),
            "--config",
            str(config),
            "--summary",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert finished.returncode == 0, finished.stderr
    assert "Verified OK" in finished.stdout
