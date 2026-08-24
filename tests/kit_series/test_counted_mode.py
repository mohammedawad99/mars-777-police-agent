"""The one value that decides whether a run may ever be counted or reported.

A rehearsal and a counted run are one flag apart in intent and irreversible in
consequence: a rehearsal that reported would mail a lecturer a result nobody
agreed to count, and a counted run that did not report would lose a played
series. These tests pin the separation, and pin that it fails closed.
"""

import pytest

from mars777_police.app.counted_mode import CountedMode, CountedRun, counted, rehearsal
from mars777_police.app.protocol_errors import LocalDefectError


def test_the_default_a_process_gets_is_a_rehearsal() -> None:
    """Nobody reaches a counted run by omission."""
    assert rehearsal().mode is CountedMode.REHEARSAL
    assert not rehearsal().is_counted
    assert not rehearsal().may_report


def test_a_counted_run_is_reached_only_by_saying_so() -> None:
    assert counted().mode is CountedMode.COUNTED
    assert counted().is_counted
    assert counted().may_report


def test_a_rehearsal_refuses_every_counted_capability_by_name() -> None:
    """The message says which capability and why, not merely that it refused."""
    with pytest.raises(LocalDefectError, match="the final report belongs to a counted run"):
        rehearsal().require_counted("the final report")
    with pytest.raises(LocalDefectError, match="never be counted or reported"):
        rehearsal().require_counted("the result artifact")


def test_a_counted_run_refuses_rehearsal_only_capabilities() -> None:
    with pytest.raises(LocalDefectError, match="belongs to a rehearsal"):
        counted().require_rehearsal("development evidence")


def test_a_counted_run_passes_its_own_gate() -> None:
    counted().require_counted("the final report")
    rehearsal().require_rehearsal("development evidence")


def test_reporting_is_asked_rather_than_derived() -> None:
    """A third mode must not inherit a branch by being `!= REHEARSAL`.

    The property under test is that `may_report` is true for exactly the counted
    mode - so a mode added later is non-reporting until someone decides
    otherwise, rather than reporting because nobody looked.
    """
    reporting = {mode for mode in CountedMode if CountedRun(mode).may_report}
    assert reporting == {CountedMode.COUNTED}


def test_the_mode_cannot_be_changed_after_the_run_starts() -> None:
    """Frozen: what a run is worth is decided once, at startup, and not revised."""
    live = counted()
    with pytest.raises(AttributeError):
        live.mode = CountedMode.REHEARSAL  # type: ignore[misc]


def test_the_two_modes_are_the_whole_vocabulary() -> None:
    assert [mode.value for mode in CountedMode] == ["REHEARSAL", "COUNTED"]
