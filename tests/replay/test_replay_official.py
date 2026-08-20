"""Replaying a real official log, over the authorities that already judged it."""

from pathlib import Path

import pytest
import replay_fixtures as fixtures

from mars777_police.sdk import AgentSdk, ReplayCheck, ReplayError, board_lines


def session(tmp_path: Path) -> object:
    log, config = fixtures.played(tmp_path)
    return AgentSdk().open_replay(log, config)


def test_a_real_sub_game_replays_every_committed_step(tmp_path: Path) -> None:
    replay = session(tmp_path)

    assert replay.steps  # type: ignore[attr-defined]
    assert [step.number for step in replay.steps] == [1, 2]  # type: ignore[attr-defined]


def test_every_commitment_recomputes_to_verified_ok(tmp_path: Path) -> None:
    """REPLAY-002's words, from the authority that owns the digest."""
    found = session(tmp_path).summary()  # type: ignore[attr-defined]

    assert found.crypto is ReplayCheck.VERIFIED_OK
    assert found.crypto.value == "Verified OK"


def test_the_replay_agrees_with_the_recorded_audit(tmp_path: Path) -> None:
    found = session(tmp_path).summary()  # type: ignore[attr-defined]

    assert found.semantic_verdict == "CONSISTENT"
    assert found.recorded_result == "Verified OK"
    assert found.outcome_agrees is True
    assert found.tampered_step is None


def test_the_replay_is_deterministic(tmp_path: Path) -> None:
    log, config = fixtures.played(tmp_path)

    once = AgentSdk().open_replay(log, config).steps
    twice = AgentSdk().open_replay(log, config).steps

    assert once == twice


def test_navigation_is_bounded_at_both_ends(tmp_path: Path) -> None:
    replay = session(tmp_path)

    assert replay.first().number == 1  # type: ignore[attr-defined]
    assert replay.previous().number == 1  # type: ignore[attr-defined]
    assert replay.last().number == 2  # type: ignore[attr-defined]
    assert replay.next().number == 2  # type: ignore[attr-defined]
    assert replay.current().number == 2  # type: ignore[attr-defined]


def test_the_board_is_drawn_for_a_human(tmp_path: Path) -> None:
    step = session(tmp_path).first()  # type: ignore[attr-defined]

    lines = board_lines(step)

    assert len(lines) == step.grid_size + 1
    assert "P" in "".join(lines) and "T" in "".join(lines)
    assert "police" in lines[-1] and "barrier" in lines[-1]


def test_the_two_agents_move_where_the_log_says_they_did(tmp_path: Path) -> None:
    replay = session(tmp_path)

    first, second = replay.steps  # type: ignore[attr-defined]

    assert first.police_cell != second.police_cell


def test_a_config_that_is_not_the_logged_one_is_refused(tmp_path: Path) -> None:
    log, config = fixtures.played(tmp_path)
    document = fixtures.document(config)
    document["config"]["board_and_agents"]["grid_size"] = 9  # type: ignore[index]
    fixtures.rewritten(config, document)

    with pytest.raises(ReplayError, match="the log was played under"):
        AgentSdk().open_replay(log, config)


def test_no_secret_reaches_a_projected_step(tmp_path: Path) -> None:
    """A nonce is disclosed evidence; a key never is, and neither is a belief."""
    replay = session(tmp_path)

    rendered = repr(replay.steps)  # type: ignore[attr-defined]

    for forbidden in ("secret", "AuthSecret", "belief", "strategy", "key_id"):
        assert forbidden not in rendered


def test_the_facade_verifies_without_opening_a_session(tmp_path: Path) -> None:
    log, config = fixtures.played(tmp_path)

    found = AgentSdk().verify_replay(log, config)

    assert found.crypto is ReplayCheck.VERIFIED_OK
    assert found.steps == 2


def test_a_commit_with_no_matching_reveal_still_replays(tmp_path: Path) -> None:
    """A turn sealed but never revealed leaves the projection's fields empty."""
    log, config = fixtures.played(tmp_path)
    document = fixtures.document(log)
    document["entries"] = [one for one in document["entries"] if one["phase"] != "reveal"]
    fixtures.rewritten(log, document)

    replay = AgentSdk().open_replay(log, config)

    assert all(turn.hint is None for step in replay.steps for turn in step.turns)


def test_a_commit_without_a_step_number_is_refused(tmp_path: Path) -> None:
    log, config = fixtures.played(tmp_path)
    document = fixtures.document(log)
    for entry in document["entries"]:
        if entry["phase"] == "commit":
            del entry["step"]
            break
    fixtures.rewritten(log, document)

    with pytest.raises(ReplayError, match="no step number"):
        AgentSdk().open_replay(log, config)
