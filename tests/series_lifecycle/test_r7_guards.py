"""What the series refuses: out-of-order lifecycle, early results, bad writes."""

import asyncio
from pathlib import Path

import boot_builders as build
import composed_builders as compose
import pytest
import r7_builders as r7
import r7_fixtures as fixtures
from r16_builders import GROUP_A, GROUP_B

from mars777_police.agent_runtime import AgentRuntime
from mars777_police.app.protocol_errors import LocalDefectError, StaleMessageError
from mars777_police.app.sealed_record_values import ActorRole
from mars777_police.app.series_record import outcome_line
from mars777_police.domain.terminal import Outcome
from mars777_police.infra.artifacts import JsonArtifactStore
from mars777_police.series_runtime import SeriesRuntime

LINES = tuple(outcome_line(n, Outcome.CAPTURE) for n in range(1, 7))


def series(tmp_path: Path) -> SeriesRuntime:
    """A composed, unserved agent with a real store - enough to test refusals."""
    composition = compose.after_step0(compose.compose())
    agent = AgentRuntime(composition, build.HOST, build.free_port())
    return r7.series_for(agent, JsonArtifactStore(tmp_path))


def test_the_declaration_waits_for_the_peers_step0(tmp_path: Path) -> None:
    agent = AgentRuntime(compose.compose(), build.HOST, build.free_port())
    fresh = r7.series_for(agent, JsonArtifactStore(tmp_path))
    with pytest.raises(LocalDefectError, match="waits for the peer"):
        fresh.record_declaration()
    assert list(tmp_path.iterdir()) == []


def test_a_config_artifact_needs_a_config_this_side_agreed(tmp_path: Path) -> None:
    runtime = series(tmp_path)
    with pytest.raises(LocalDefectError, match="config this side agreed"):
        runtime.lock_config(r7.CONFIG)


def test_a_config_artifact_refuses_a_config_that_is_not_the_locked_one(tmp_path: Path) -> None:
    runtime = series(tmp_path)
    r7.open_config(runtime, GROUP_A, 1)
    with pytest.raises(LocalDefectError, match="not the locked one"):
        runtime.lock_config(fixtures.other_config())
    assert list(tmp_path.iterdir()) == []


def test_a_sub_game_binds_only_its_own_runtimes(tmp_path: Path) -> None:
    runtime = series(tmp_path)
    with pytest.raises(LocalDefectError, match="not sub-game 1"):
        runtime.open_sub_game(
            r7.evidence_for(ActorRole.POLICE, 2), r7.audit_for(ActorRole.THIEF, GROUP_B, 2)
        )


def test_closing_a_sub_game_needs_a_bound_audited_sub_game(tmp_path: Path) -> None:
    runtime = series(tmp_path)
    with pytest.raises(StaleMessageError):
        runtime.close_sub_game(Outcome.CAPTURE)


def test_a_second_close_of_the_same_sub_game_is_refused(tmp_path: Path) -> None:
    runtime = series(tmp_path)
    runtime.open_sub_game(
        r7.evidence_for(ActorRole.POLICE, 1), r7.audit_for(ActorRole.THIEF, GROUP_B, 1)
    )
    runtime.lines = LINES[:1]
    with pytest.raises(LocalDefectError, match="already recorded"):
        runtime.close_sub_game(Outcome.CAPTURE)


def test_a_result_needs_all_six_sub_games(tmp_path: Path) -> None:
    runtime = series(tmp_path)
    runtime.lines = LINES[:5]
    with pytest.raises(LocalDefectError, match="recorded once each"):
        runtime.build_result()
    assert list(tmp_path.iterdir()) == []


def test_a_result_needs_a_complete_series_audit(tmp_path: Path) -> None:
    """Six lines are not enough: the gate answers `None` until six audits exist."""
    runtime = series(tmp_path)
    runtime.lines = LINES
    with pytest.raises(StaleMessageError):
        runtime.build_result()
    assert list(tmp_path.iterdir()) == []


def test_persisting_a_result_needs_the_agreement_to_have_completed(tmp_path: Path) -> None:
    runtime = series(tmp_path)
    runtime.lines = LINES
    fixtures.unagreed_result(runtime)
    with pytest.raises(LocalDefectError, match="waits for a mutual agreement"):
        runtime.persist_result()
    assert list(tmp_path.iterdir()) == []


def test_a_replace_failure_leaves_no_official_artifact(tmp_path: Path, monkeypatch) -> None:
    """The atomic move is the last step; if it fails, nothing is presented as official."""
    store = JsonArtifactStore(tmp_path)

    def refuse(source: object, target: object) -> None:
        raise OSError("the rename could not complete")

    monkeypatch.setattr("mars777_police.infra.artifacts.os.replace", refuse)
    with pytest.raises(OSError, match="rename"):
        store.store("result_x.json", {"a": 1})
    assert list(tmp_path.iterdir()) == []


def test_the_series_connects_only_when_it_is_still_serving(tmp_path: Path) -> None:
    """`start` dials once; a runtime that is already running is left alone."""
    runtime = series(tmp_path)
    with pytest.raises(Exception, match=r"E-TRANSPORT|refused|attempts"):
        asyncio.run(runtime.start())
