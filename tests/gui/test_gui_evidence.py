"""The two submission screenshots, produced by the real GUI from a real match.

`DOC-001` asks for a live belief-map picture and a replay picture showing the
verification result. Both come from one thirty-five-round sub-game that two
composed agents actually played here - the live one from the snapshot the police
driver published on its last lawful turn, the replay one from the official log
that same sub-game wrote. Nothing is drawn by hand and nothing is staged.

The files are written into the repository only when asked for, so an ordinary
test run asserts the pictures without touching a single committed byte.
"""

import os
from pathlib import Path

import gui_evidence_run as run
import pytest

from mars777_police.app.live_view_values import LiveViewSnapshot
from mars777_police.app.replay_status import audit_complete
from mars777_police.app.replay_values import ReplayCheck, ReplayStep
from mars777_police.gui.image_renderer import write_png
from mars777_police.gui.live_layout import BELIEF_LABEL, live_frame
from mars777_police.gui.primitives import Frame
from mars777_police.gui.replay_app import frame_for

WRITE = "MARS777_WRITE_GUI_EVIDENCE"
LIVE_SHOT = "live_belief_map.png"
REPLAY_SHOT = "replay_verified.png"


@pytest.fixture(scope="module")
def match(tmp_path_factory: pytest.TempPathFactory) -> tuple[LiveViewSnapshot, Path]:
    """One real sub-game, played once and read by every test in this file."""
    root = tmp_path_factory.mktemp("evidence")
    seen, _, _ = run.played(root)
    return seen, root


def where(name: str) -> Path:
    """Where a committed screenshot lives in this repository."""
    return Path(__file__).resolve().parents[2] / "docs" / "evidence" / "gui" / name


def keep(frame: Frame, name: str) -> None:
    """Write the picture into the repository, but only when asked to."""
    if os.environ.get(WRITE) == "1":
        write_png(frame, where(name))


def test_the_live_picture_shows_a_real_belief_map_and_no_opponent(
    match: tuple[LiveViewSnapshot, Path],
) -> None:
    seen, _ = match
    assert seen.has_belief, "thirty-five rounds must have folded some disclosed evidence"
    frame = live_frame(seen)
    assert BELIEF_LABEL in frame.labels()
    assert "LOCAL TRUTH ONLY" in frame.labels()
    assert "opponent position: never shown" in frame.labels()
    keep(frame, LIVE_SHOT)


def test_the_replay_picture_shows_the_verification_the_authorities_reached(
    match: tuple[LiveViewSnapshot, Path],
) -> None:
    _, root = match
    session = run.session(root)
    summary = session.summary()
    assert summary.crypto is ReplayCheck.VERIFIED_OK
    assert audit_complete(summary) is True
    shown = _distinct(session.steps) or session.last()
    frame = frame_for(shown, summary)
    assert any(ReplayCheck.VERIFIED_OK.value in line for line in frame.labels())
    keep(frame, REPLAY_SHOT)


def _distinct(steps: tuple[ReplayStep, ...]) -> ReplayStep | None:
    """The last step where the two agents stood apart, so both paths are visible.

    `PRD07-FR-023` is the permission this picture exercises, and a step where
    both agents happen to share one square would show it exercising nothing.
    """
    apart = [step for step in steps if step.police_cell != step.thief_cell]
    return apart[-1] if apart else None


def test_every_commitment_of_a_whole_lockstep_sub_game_verifies(
    match: tuple[LiveViewSnapshot, Path],
) -> None:
    _, root = match
    session = run.session(root)
    checks = {turn.check for step in session.steps for turn in step.turns}
    roles = {turn.role for step in session.steps for turn in step.turns}
    assert checks == {ReplayCheck.VERIFIED_OK}
    assert roles == {"police", "thief"}


def test_both_committed_screenshots_are_present_and_are_real_images() -> None:
    for name in (LIVE_SHOT, REPLAY_SHOT):
        assert where(name).exists(), f"{name} has never been generated"
        assert where(name).read_bytes().startswith(b"\x89PNG"), name
