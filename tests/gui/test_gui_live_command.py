"""Watching a live match: the series on one thread, the window on another.

The point of the arrangement is that the window is a spectator. These tests
check that the series is handed the sink and nothing else, that the window never
runs on the game's thread, and that a series which fails is still reported by a
process whose window has already closed.
"""

import threading
from pathlib import Path

import gui_toolkit_doubles as toolkit
import pytest

from mars777_police import gui_main
from mars777_police.app.live_view_sink import LatestSnapshot
from mars777_police.operator_requests import StrictSeriesRequest


class Series:
    """A stand-in facade that records the request and the thread it ran on."""

    def __init__(self, blow_up: bool = False) -> None:
        self.blow_up = blow_up
        self.seen: StrictSeriesRequest | None = None
        self.thread: str | None = None

    async def run_strict_series(self, request: StrictSeriesRequest) -> Path:
        """Record what the viewer was handed, then finish or fail as asked."""
        self.seen = request
        self.thread = threading.current_thread().name
        if self.blow_up:
            raise RuntimeError("the peer never answered")
        return Path("artifacts")


@pytest.fixture
def toolkit_roots(monkeypatch: pytest.MonkeyPatch) -> list[toolkit.FakeRoot]:
    """The toolkit replaced by recorders, so this runs without a display."""
    return toolkit.install(monkeypatch)


def run(monkeypatch: pytest.MonkeyPatch, series: Series) -> int:
    """Run the live command against *series*."""
    monkeypatch.setattr(gui_main, "AgentSdk", lambda: series)
    return gui_main.main(["live", "--launch", "launch.json"])


def test_the_series_is_handed_a_one_slot_sink_and_the_launch_it_was_given(
    toolkit_roots: list[toolkit.FakeRoot], monkeypatch: pytest.MonkeyPatch
) -> None:
    series = Series()

    assert run(monkeypatch, series) == 0

    assert series.seen is not None
    assert isinstance(series.seen.viewer, LatestSnapshot)
    assert series.seen.launch == Path("launch.json")


def test_the_match_runs_on_its_own_thread_rather_than_the_window_s(
    toolkit_roots: list[toolkit.FakeRoot], monkeypatch: pytest.MonkeyPatch
) -> None:
    series = Series()

    run(monkeypatch, series)

    assert series.thread == "series"
    assert series.thread != threading.current_thread().name


def test_the_window_is_opened_and_given_the_toolkit_s_own_loop(
    toolkit_roots: list[toolkit.FakeRoot], monkeypatch: pytest.MonkeyPatch
) -> None:
    run(monkeypatch, Series())

    assert toolkit_roots[0].looped == 1
    assert toolkit_roots[0].bindings == {}


def test_a_series_that_fails_is_reported_rather_than_swallowed(
    toolkit_roots: list[toolkit.FakeRoot],
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    capsys.readouterr()

    status = run(monkeypatch, Series(blow_up=True))

    assert status == 2
    assert "the peer never answered" in capsys.readouterr().err
