"""The counted gateway must report the series it just wrote, and only then.

`SeriesDriver._report` covers the fixed-role path, where one process plays the
whole series. An alternating counted series never reaches it - the group's two
backends each hold three sub-games and only the gateway holds the series - so a
real counted game against `s82kma9e` wrote all fourteen files and mailed nobody.

These drive `series_writer` exactly as `compose_gateway` does, with an injected
reporter, so nothing here can reach Gmail or a lecturer.
"""

from pathlib import Path
from typing import Any

from executable_process import environment, written_launch
from r16_builders import merged

from mars777_police.app.counted_mode import counted, rehearsal
from mars777_police.app.kit_messages import KitRole
from mars777_police.app.kit_settled_row import settled_row
from mars777_police.app.official_artifacts import CONFIG, LOG, OfficialArtifactCollector
from mars777_police.app.sealed_record_values import ActorRole
from mars777_police.app.series_assembly import SeriesParts
from mars777_police.app.series_result_owner import SeriesResultOwner
from mars777_police.compose_series_writer import series_writer
from mars777_police.domain.terminal import Outcome
from mars777_police.infra.settings import load_runtime_settings
from mars777_police.operator_requests import PublicGatewayRequest

DIGEST = "9b0e173a79212271dea3f3b546591d7f93fe476ef7e7572aca34f8e88bccc142"


class Recorder:
    """A reporter that records what it was handed, and sends nothing at all."""

    def __init__(self) -> None:
        self.calls: list[Path] = []

    def __call__(self, result: Path) -> None:
        self.calls.append(result)


def parts(*, agreed: str | None = DIGEST, rows: int = 6) -> SeriesParts:
    collected = OfficialArtifactCollector()
    for number in range(1, 7):
        collected.record(CONFIG, number, {"config": {}, "sub_game": number})
        collected.record(LOG, number, {"entries": [], "sub_game": number})
    settlement = SeriesResultOwner()
    if agreed is not None:
        settlement.settle(agreed)
    declaration = merged()
    seated = declaration.teams.group_a
    other = declaration.teams.group_b
    assert seated is not None and other is not None
    return SeriesParts(
        declaration=declaration,
        collected=collected,
        rows=tuple(
            settled_row(
                sub_game=n,
                ours=seated.group_id,
                theirs=other.group_id,
                our_role=KitRole.POLICE if n % 2 else KitRole.THIEF,
                outcome=Outcome.SURVIVAL,
            )
            for n in range(1, rows + 1)
        ),
        settlement=settlement,
    )


def writer(root: Path, reporter: Any, *, is_counted: bool = True) -> Any:
    """`series_writer` exactly as `compose_gateway` builds it, minus the mail."""
    settings = load_runtime_settings(environment(root=root), expected_role=ActorRole.POLICE)
    request = PublicGatewayRequest(
        police_endpoint="http://127.0.0.1:8811/mcp",
        thief_endpoint="http://127.0.0.1:8812/mcp",
        ngrok=Path("/nonexistent/ngrok"),
        launch=written_launch(root),
        counted=is_counted,
    )
    return series_writer(settings, request, reporter=reporter)


def test_a_completed_counted_series_reports_itself_with_no_operator_command(
    tmp_path: Path,
) -> None:
    reporter = Recorder()
    write = writer(tmp_path, reporter)
    assert write is not None
    written = write(parts())
    assert written is not None and len(written) == 14
    assert len(reporter.calls) == 1


def test_the_reporter_is_handed_the_result_that_was_actually_written(tmp_path: Path) -> None:
    reporter = Recorder()
    write = writer(tmp_path, reporter)
    assert write is not None
    write(parts())
    handed = reporter.calls[0]
    assert handed.name == f"result_{merged().game_id}.json"
    assert handed.is_file()


def test_a_rehearsal_writes_nothing_and_can_never_report(tmp_path: Path) -> None:
    """The run class decides before boot; a rehearsal has no writer at all."""
    reporter = Recorder()
    assert writer(tmp_path, reporter, is_counted=False) is None
    assert reporter.calls == []
    assert rehearsal().may_report is False
    assert counted().may_report is True


def test_a_series_still_missing_a_row_reports_nothing(tmp_path: Path) -> None:
    reporter = Recorder()
    write = writer(tmp_path, reporter)
    assert write is not None
    assert write(parts(rows=5)) is None
    assert reporter.calls == []


def test_a_series_whose_settlement_never_agreed_reports_nothing(tmp_path: Path) -> None:
    """Rule 35 scores an unagreed series 0 for both groups; it is not mailed."""
    reporter = Recorder()
    write = writer(tmp_path, reporter)
    assert write is not None
    assert write(parts(agreed=None)) is None
    assert reporter.calls == []


def test_the_reporter_is_asked_once_per_completed_series(tmp_path: Path) -> None:
    """Every contribution asks the assembler; only the completing one reports."""
    reporter = Recorder()
    write = writer(tmp_path, reporter)
    assert write is not None
    write(parts(rows=4))
    write(parts(rows=5))
    write(parts())
    assert len(reporter.calls) == 1


def test_a_provider_failure_never_propagates_into_the_written_series(tmp_path: Path) -> None:
    """The game is over and on disk before the reporter runs; delivery may fail."""

    def refuses(result: Path) -> None:
        raise RuntimeError("provider refused")

    write = writer(tmp_path, refuses)
    assert write is not None
    written = write(parts())
    assert written is not None and len(written) == 14
    assert (tmp_path / f"result_{merged().game_id}.json").is_file()
