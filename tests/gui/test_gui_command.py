"""The graphical command line: a picture to a file, or a window on a screen.

`--png` is what makes the GUI provable where there is no display - the same
frame the window would draw, written as a file - and it is how the submission
screenshots are produced. The exit status is the replay viewer's, unchanged.
"""

import os
from pathlib import Path

import gui_toolkit_doubles as toolkit
import pytest
import replay_fixtures as evidence
from PIL import Image

from mars777_police import gui_main


def argv(tmp_path: Path, *extra: str) -> list[str]:
    """A replay command over a sub-game two real agents just played."""
    log, config = evidence.played(tmp_path)
    return ["replay", "--log", str(log), "--config", str(config), *extra]


def test_writing_a_picture_needs_no_display_and_reports_where_it_went(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    target = tmp_path / "shot.png"
    command = argv(tmp_path, "--png", str(target))
    capsys.readouterr()

    status = gui_main.main(command)
    printed = capsys.readouterr().out

    assert status == 0
    assert str(target) in printed
    with Image.open(target) as written:
        assert written.format == "PNG"


def test_the_picture_can_be_asked_for_a_particular_step(tmp_path: Path) -> None:
    first, later = tmp_path / "one.png", tmp_path / "two.png"
    command = argv(tmp_path)
    gui_main.main([*command, "--png", str(first), "--step", "1"])
    gui_main.main([*command, "--png", str(later), "--step", "2"])
    assert first.read_bytes() != later.read_bytes()


def test_unreadable_evidence_is_a_sentence_and_status_two(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    capsys.readouterr()

    status = gui_main.main(
        ["replay", "--log", str(tmp_path / "nope.json"), "--config", str(tmp_path / "no.json")]
    )

    assert status == 2
    assert "cannot replay" in capsys.readouterr().err


def test_a_window_opens_when_no_file_was_asked_for(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    roots = toolkit.install(monkeypatch)

    assert gui_main.main(argv(tmp_path)) == 0
    assert roots[0].looped == 1
    assert set(roots[0].bindings) == {"<Right>", "<Left>", "<Home>", "<End>"}


def test_the_command_refuses_an_unknown_mode_rather_than_guessing() -> None:
    with pytest.raises(SystemExit):
        gui_main.parse_args(["draw"])


def test_both_modes_are_offered_and_each_names_what_it_needs() -> None:
    replay = gui_main.parse_args(["replay", "--log", "a", "--config", "b"])
    live = gui_main.parse_args(["live", "--launch", "c"])
    assert (replay.mode, live.mode) == ("replay", "live")
    assert replay.png is None and replay.root is None
    assert live.launch == Path("c")


def test_the_viewer_is_runnable_as_a_module(tmp_path: Path) -> None:
    """`uv run python -m …gui_main` really is the entry point, with no display."""
    import subprocess
    import sys

    target = tmp_path / "module.png"
    command = argv(tmp_path, "--png", str(target))
    finished = subprocess.run(
        [sys.executable, "-m", "mars777_police.gui_main", *command],
        capture_output=True,
        text=True,
        check=False,
        env={**os.environ, "DISPLAY": ""},
    )

    assert finished.returncode == 0, finished.stderr
    assert target.exists()
