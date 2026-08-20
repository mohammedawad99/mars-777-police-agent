"""Two real agents play a whole sub-game while the window is on fire.

The strongest form of `PRD07-FR-008`: not that a sink swallows an exception, but
that the production driver reaches the same terminal, in the same number of
rounds, whether nobody is watching, somebody is, or the somebody is broken.
"""

import asyncio
from pathlib import Path

import autonomous_builders as harness
import pytest
from test_live_isolation import Angry

from mars777_police.app.live_view_feed import LiveViewFeed
from mars777_police.app.live_view_sink import LatestSnapshot, LiveViewSink
from mars777_police.app.sealed_record_values import ActorRole
from mars777_police.app.sub_game_driver import SubGameDriver
from mars777_police.domain.terminal import Outcome
from mars777_police.series_runtime import SeriesRuntime

GAME = "MaRs-777-vs-peer"


def play(watch: pytest.MonkeyPatch, root: Path, viewer: LiveViewSink | None) -> tuple[Outcome, int]:
    """One whole natural sub-game, with *viewer* attached to the police driver."""
    built = harness.driver_for

    def attach(series: SeriesRuntime, role: ActorRole) -> SubGameDriver:
        driver = built(series, role)
        if viewer is not None and role is ActorRole.POLICE:
            driver.feed = LiveViewFeed(viewer, role.value, GAME)
        return driver

    watch.setattr(harness, "driver_for", attach)
    a, b = harness.pair_for(root)
    return asyncio.run(harness.autonomous(a, b))


def test_a_broken_window_changes_neither_the_outcome_nor_the_round_count(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    unwatched = play(monkeypatch, tmp_path / "alone", None)
    broken = play(monkeypatch, tmp_path / "broken", Angry())
    assert broken == unwatched


def test_a_working_window_sees_the_last_lawful_turn_of_a_real_sub_game(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    box = LatestSnapshot()
    outcome, rounds = play(monkeypatch, tmp_path / "watched", box)
    seen = box.take()
    assert seen is not None
    assert box.published == rounds
    assert seen.role == ActorRole.POLICE.value
    assert seen.game_id == GAME
    assert seen.step == rounds
    assert outcome is not None
