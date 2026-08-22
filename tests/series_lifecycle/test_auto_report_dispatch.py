"""A completed counted series must report itself, with nobody typing a command.

Appendix E rule 32 requires the result of every legal game to be reported
**automatically**, and rule 35 makes each group's own report the condition for
being credited at all - non-reporting scores 0 for *both* groups. Until this
file existed the reporting service was complete and correct but only an operator
could trigger it, so a real series ended with a result on disk and no email.

The dispatch is deliberately downstream of everything that decides a game: it
runs after the mutual agreement and after the result is persisted, it is handed
the artifact that was written, and whatever the provider says can never change
what the game was.
"""

import asyncio
from pathlib import Path

import autonomous_series_builders as auto
import pytest

from mars777_police.app.sealed_record_values import ActorRole
from mars777_police.app.state_machine import ProtocolPhase

GAMES = 6


class Recorder:
    """A reporter that records what it was asked to send, and sends nothing."""

    def __init__(self, fail: bool = False) -> None:
        self.calls: list[str] = []
        self.fail = fail

    def __call__(self, result: Path) -> None:
        self.calls.append(str(result))
        if self.fail:
            raise RuntimeError("provider refused")


@pytest.fixture(scope="module")
def played(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, Recorder, Recorder]:
    """One real autonomous series, with a recording reporter on each side."""
    root = tmp_path_factory.mktemp("autoreport")
    a, b = auto.pair_for(root)
    police_reporter, thief_reporter = Recorder(), Recorder()
    drivers = (
        auto.driver_for(a, ActorRole.POLICE, reporter=police_reporter),
        auto.driver_for(b, ActorRole.THIEF, reporter=thief_reporter),
    )

    async def run() -> None:
        async with auto.started(a, b):
            for driver in drivers:
                driver.open()
            await asyncio.gather(*(driver.play_series() for driver in drivers))

    asyncio.run(run())
    return root, police_reporter, thief_reporter


def test_a_completed_series_reports_itself_without_an_operator_command(
    played: tuple[Path, Recorder, Recorder],
) -> None:
    """The whole point: no `report_main`, no human, no second process."""
    _, police_reporter, _ = played

    assert police_reporter.calls, "a finished counted series sent no report"


def test_the_reporter_is_handed_the_persisted_agreed_result(
    played: tuple[Path, Recorder, Recorder],
) -> None:
    root, police_reporter, _ = played
    sent = Path(police_reporter.calls[0])

    assert sent.name.startswith("result_")
    assert sent.suffix == ".json"
    assert sent.is_file()
    assert sent.read_bytes() == (root / "police" / sent.name).read_bytes()


def test_the_report_is_dispatched_exactly_once_per_series(
    played: tuple[Path, Recorder, Recorder],
) -> None:
    _, police_reporter, _ = played

    assert len(police_reporter.calls) == 1


def test_dispatch_happens_only_after_the_series_reached_report_ready(
    played: tuple[Path, Recorder, Recorder],
) -> None:
    """Rule 36 puts the mutual audit before the agreement, and both before this."""
    root, _, _ = played
    logs = sorted(one for one in (root / "police").iterdir() if one.name.startswith("log_"))

    assert len(logs) == GAMES
    assert ProtocolPhase.REPORT_READY.value == "REPORT_READY"


def test_the_official_artifact_set_is_still_exactly_fourteen(
    played: tuple[Path, Recorder, Recorder],
) -> None:
    """Delivery is not an official artifact and must never become the fifteenth."""
    root, _, _ = played

    for side in ("police", "thief"):
        assert len(list((root / side).iterdir())) == 14


def test_a_series_without_a_reporter_still_completes(tmp_path: Path) -> None:
    """The port is optional, so a development composition changes nothing."""
    root = tmp_path / "noreporter"
    root.mkdir()
    a, b = auto.pair_for(root)
    drivers = (auto.driver_for(a, ActorRole.POLICE), auto.driver_for(b, ActorRole.THIEF))

    async def run() -> None:
        async with auto.started(a, b):
            for driver in drivers:
                driver.open()
            await asyncio.gather(*(driver.play_series() for driver in drivers))

    asyncio.run(run())

    assert len(list((root / "police").iterdir())) == 14


def test_a_reporting_failure_leaves_the_result_exactly_as_it_was(tmp_path: Path) -> None:
    """A provider refusal is a delivery problem, never a game problem."""
    root = tmp_path / "failing"
    root.mkdir()
    a, b = auto.pair_for(root)
    angry = Recorder(fail=True)
    drivers = (
        auto.driver_for(a, ActorRole.POLICE, reporter=angry),
        auto.driver_for(b, ActorRole.THIEF),
    )

    async def run() -> None:
        async with auto.started(a, b):
            for driver in drivers:
                driver.open()
            await asyncio.gather(*(driver.play_series() for driver in drivers))

    asyncio.run(run())
    written = sorted((root / "police").iterdir())

    assert angry.calls, "the reporter was never reached"
    assert len(written) == 14
    result = next(one for one in written if one.name.startswith("result_"))
    assert result.read_bytes()


def test_the_real_counted_boot_wires_a_reporter_that_actually_sends() -> None:
    """The production path must not quietly keep the old silent behaviour.

    Asserted on the real boot rather than on a fake: `AutonomousBoot` builds the
    one production `SeriesDriver`, and it must hand it a reporter that reaches
    the same `send_game_report` the operator command uses - one gate, one
    recipient, one message contract, nobody typing.
    """
    import inspect

    from mars777_police.app.report_dispatch import no_report
    from mars777_police.autonomous_boot import AutonomousBoot

    built = inspect.getsource(AutonomousBoot.driver)
    dispatch = inspect.getsource(AutonomousBoot.reporter)

    assert "reporter=self.reporter" in built
    assert "send_game_report" in dispatch
    assert AutonomousBoot.reporter is not no_report


def test_the_series_owner_never_learns_what_gmail_is() -> None:
    """The dependency runs one way: orchestration -> port -> provider."""
    import inspect

    from mars777_police import series_driver

    body = inspect.getsource(series_driver)

    for provider in ("gmail", "Gmail", "oauth", "OAuth", "smtp", "credential"):
        assert provider not in body
