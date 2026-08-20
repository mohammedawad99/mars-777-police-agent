"""The replay picture, over a sub-game two real agents actually played.

`PRD07-FR-023` allows the replay - and only the replay - to show both agents'
true paths, so these tests demand what the live tests forbid. Everything on
screen still comes from `ReplaySession` and `audit_complete`; the layout adds no
verdict of its own.
"""

from pathlib import Path

import pytest
import replay_fixtures as evidence

from mars777_police.app.replay_session import ReplaySession
from mars777_police.app.replay_values import ReplayCheck, ReplaySummary
from mars777_police.compose_replay import open_replay
from mars777_police.gui.geometry import fit
from mars777_police.gui.palette import POLICE, THIEF, status_glyph
from mars777_police.gui.replay_app import frame_for
from mars777_police.gui.replay_layout import OFFICIAL, REPLAY, replay_frame


@pytest.fixture
def session(tmp_path: Path) -> ReplaySession:
    """A replay over the official log and config a real sub-game produced."""
    log, config = evidence.played(tmp_path)
    return open_replay(log, config, tmp_path)


def test_the_banner_says_replay_and_official_so_nothing_reads_as_live(
    session: ReplaySession,
) -> None:
    words = " ".join(frame_for(session.first(), session.summary()).labels())
    assert REPLAY in words
    assert OFFICIAL in words
    assert "LIVE" not in words


def test_both_agents_are_drawn_because_the_audit_point_has_passed(
    session: ReplaySession,
) -> None:
    step = session.first()
    frame = replay_frame(step, session.summary(), True)
    geometry = fit(step.grid_size, frame.width, frame.height)
    for cell, colour in ((step.police_cell, POLICE), (step.thief_cell, THIEF)):
        drawn = [rect for rect in frame.rects if rect.fill == colour]
        assert len(drawn) == 1
        left, top, _, _ = geometry.cell_box(*cell)
        assert (drawn[0].left, drawn[0].top) == (left, top)
    assert {"P", "T"} <= set(frame.labels())


def test_every_verification_word_is_shown_with_its_own_glyph(
    session: ReplaySession,
) -> None:
    step = session.first()
    words = frame_for(step, session.summary()).labels()
    for turn in step.turns:
        assert any(
            turn.check.value in line and status_glyph(turn.check.value) in line for line in words
        )


def test_the_panel_repeats_the_verdicts_the_authorities_already_reached(
    session: ReplaySession,
) -> None:
    summary = session.summary()
    words = " ".join(frame_for(session.first(), summary).labels())
    assert summary.crypto.value in words
    assert summary.recorded_result in words
    assert summary.evidence_class in words
    assert "audit complete" in words


def test_every_step_of_a_real_log_draws_without_a_special_case(
    session: ReplaySession,
) -> None:
    summary = session.summary()
    step = session.first()
    for number in range(summary.steps):
        frame = frame_for(step, summary)
        assert frame.width > 0 and frame.height > 0
        assert any(f"step {step.number} of {summary.steps}" in one for one in frame.labels())
        if number + 1 < summary.steps:
            step = session.next()


def test_a_declared_barrier_is_drawn_and_a_shared_cell_shows_both_agents() -> None:
    from mars777_police.app.replay_values import ReplayStep
    from mars777_police.gui.palette import BARRIER, BOTH
    from mars777_police.gui.replay_layout import replay_frame

    step = ReplayStep(
        number=1,
        turns=(),
        police_cell=(2, 2),
        thief_cell=(2, 2),
        barriers=((0, 1), (1, 1)),
        grid_size=5,
        semantic="CONSISTENT",
    )
    frame = replay_frame(step, _summary(), True)

    assert len([rect for rect in frame.rects if rect.fill == BARRIER]) == 2
    assert len([rect for rect in frame.rects if rect.fill == BOTH]) == 1
    assert "P+T" in frame.labels()
    assert "#" in frame.labels()


def _summary() -> ReplaySummary:
    """A minimal summary, so the panel has the words it prints."""
    return ReplaySummary(
        game_id="A-vs-B",
        game_uid="u",
        sub_game=1,
        config_sha256="a" * 64,
        steps=1,
        crypto=ReplayCheck.VERIFIED_OK,
        recorded_result="Verified OK",
        tampered_step=None,
        semantic_verdict="CONSISTENT",
        outcome_agrees=True,
        evidence_class="OFFICIAL",
        notes=(),
    )
