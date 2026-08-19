"""The artifact store, the ledger and the derivations, each refused at its edges."""

from pathlib import Path

import pytest
import r7_fixtures as fixtures
from r16_builders import GROUP_A, GROUP_B

from mars777_police.app.artifact_store import (
    InvalidArtifactNameError,
    config_name,
    declaration_name,
    log_name,
    require_game_id,
    result_name,
    sub_game_token,
)
from mars777_police.app.protocol_errors import LocalDefectError
from mars777_police.app.series_record import (
    contribution_of,
    cumulative_of,
    links_of,
    outcome_line,
    own_team,
    require_complete,
)
from mars777_police.app.token_accounting import InvalidTokenUsageError, SeriesTokenLedger
from mars777_police.domain.terminal import Outcome
from mars777_police.infra.artifacts import SUFFIX, JsonArtifactStore, serialize

LINES = tuple(outcome_line(n, Outcome.CAPTURE) for n in range(1, 7))


def test_the_official_filenames_are_the_frozen_patterns() -> None:
    assert declaration_name("g-1") == "declaration_g-1.json"
    assert config_name("g-1", 2) == "config_g-1_g02.json"
    assert log_name("g-1", 6) == "log_g-1_g06.json"
    assert result_name("g-1") == "result_g-1.json"


@pytest.mark.parametrize("bad", ["", "../escape", "a/b", "with space", "dot.json"])
def test_a_game_id_that_could_leave_the_root_is_refused(bad: str) -> None:
    """`UPPER` left this list at 8A-2G: JDEC-005's format is the project's, and a
    lowercase-only rule could not name a game containing our own `MaRs-777`.
    Every refusal that protects the artifact root is unchanged - see
    `test_game_id_compatibility.py` for the full traversal set."""
    with pytest.raises(InvalidArtifactNameError):
        require_game_id(bad)


@pytest.mark.parametrize("bad", [0, 7, True, "1"])
def test_only_a_real_sub_game_gets_a_token(bad: object) -> None:
    with pytest.raises(InvalidArtifactNameError):
        sub_game_token(bad)  # type: ignore[arg-type]


def test_writing_twice_with_the_same_content_is_idempotent(tmp_path: Path) -> None:
    store = JsonArtifactStore(tmp_path / "out")
    first = store.store("declaration_x.json", {"a": 1})
    second = store.store("declaration_x.json", {"a": 1})
    assert first == second
    assert Path(first.path).read_bytes() == serialize({"a": 1})


def test_a_contradictory_official_artifact_is_refused(tmp_path: Path) -> None:
    store = JsonArtifactStore(tmp_path)
    store.store("result_x.json", {"a": 1})
    with pytest.raises(LocalDefectError, match="different content"):
        store.store("result_x.json", {"a": 2})
    assert Path(tmp_path / "result_x.json").read_bytes() == serialize({"a": 1})


def test_a_successful_write_leaves_no_partial_file(tmp_path: Path) -> None:
    JsonArtifactStore(tmp_path).store("log_x_g01.json", {"entries": []})
    assert [path.name for path in tmp_path.iterdir()] == ["log_x_g01.json"]
    assert not list(tmp_path.glob(f"*{SUFFIX}"))


def test_a_failing_write_leaves_neither_a_partial_nor_a_target(tmp_path: Path) -> None:
    """Unserializable content fails before anything can be presented as official."""
    store = JsonArtifactStore(tmp_path)
    with pytest.raises(TypeError):
        store.store("config_x_g01.json", {"bad": object()})
    assert list(tmp_path.iterdir()) == []


def test_the_ledger_counts_only_real_non_negative_usage() -> None:
    ledger = SeriesTokenLedger()
    assert ledger.usage(1) == 0
    ledger.charge(1, 10)
    ledger.charge(1, 5)
    assert (ledger.usage(1), ledger.total()) == (15, 15)
    for bad in (True, -1, "3"):
        with pytest.raises(InvalidTokenUsageError):
            ledger.charge(1, bad)  # type: ignore[arg-type]
    with pytest.raises(InvalidTokenUsageError):
        ledger.charge(7, 1)
    with pytest.raises(InvalidTokenUsageError):
        ledger.usage(0)


def test_a_technical_loss_scores_zero_and_zero() -> None:
    line = outcome_line(3, Outcome.TECHNICAL_LOSS)
    assert (line.cop_score, line.thief_score, line.outcome) == (0, 0, Outcome.TECHNICAL_LOSS)


@pytest.mark.parametrize(
    "played", [(1, 2, 3, 4, 5), (1, 2, 3, 4, 5, 5), (1, 2, 3, 4, 5, 7), (2, 1, 3, 4, 5, 6)]
)
def test_an_incomplete_or_repeated_series_cannot_be_reported(played: tuple[int, ...]) -> None:
    lines = tuple(outcome_line(n, Outcome.CAPTURE) for n in played)
    with pytest.raises(LocalDefectError, match="recorded once each"):
        require_complete(lines)


def test_the_cumulative_totals_are_derived_from_the_six_lines() -> None:
    assert cumulative_of(LINES) == fixtures.cumulative_reference(LINES)
    mixed = (*LINES[:5], outcome_line(6, Outcome.SURVIVAL))
    assert cumulative_of(mixed).series_outcome == "cop"
    tied = tuple(outcome_line(n, Outcome.TECHNICAL_LOSS) for n in range(1, 7))
    assert cumulative_of(tied).series_outcome == "tie"


def test_the_contribution_restates_one_declared_commit_for_all_six() -> None:
    declaration = fixtures.merged_declaration()
    ledger = SeriesTokenLedger()
    ledger.charge(2, 40)
    contribution = contribution_of(declaration, GROUP_A, LINES, ledger)
    commit = own_team(declaration, GROUP_A).github_commit
    assert [entry.sub_game for entry in contribution.entries] == [1, 2, 3, 4, 5, 6]
    assert {entry.github_commit for entry in contribution.entries} == {commit}
    assert [entry.tokens for entry in contribution.entries] == [0, 40, 0, 0, 0, 0]


def test_the_four_links_come_from_the_two_declared_teams() -> None:
    declaration = fixtures.merged_declaration()
    links = links_of(declaration)
    assert links.group_a_police == own_team(declaration, GROUP_A).repos.police
    assert links.group_b_thief == own_team(declaration, GROUP_B).repos.thief


def test_a_partial_declaration_cannot_report_a_result() -> None:
    partial = fixtures.partial_declaration()
    with pytest.raises(LocalDefectError, match="merged declaration"):
        links_of(partial)


def test_the_declaration_document_round_trips_through_the_launch_parser() -> None:
    """What we write is what the frozen wire contract already accepts."""
    assert fixtures.declaration_round_trip(fixtures.merged_declaration()) is True
