"""The sub-game cursor and the one branch the orchestrator genuinely owns.

`STATE_MACHINE.md` §1 draws the boundary as "SUBGAME_COMPLETE -> (next sub-game
-> READY)" and gives SERIES_COMPLETE the entry condition "all sub-games played
(`num_games`=6 FIXED)". The orchestrator owns the cursor, so it can decide that
branch from authoritative facts instead of trusting a caller boolean: continuing
requires an unplayed sub-game, and ending requires the last one.

Advancement happens **only** on the SUBGAME_COMPLETE -> READY edge. Entering
SUBGAME_COMPLETE - by capture, survival, max_moves or technical loss - never
moves the cursor, so a technical loss produces exactly the same cursor sequence
as an ordinary completion (`STATE_MACHINE.md` §4).
"""

import itertools

import pytest

from mars777_police.app.orchestrator import IllegalSubGameBranchError, LocalOrchestrator
from mars777_police.app.state_machine import ProtocolMachine, ProtocolPhase
from mars777_police.domain.config_model import InvalidSeriesError, SeriesConfig

P = ProtocolPhase
SERIES = SeriesConfig()
TO_READY = (P.STEP0_NEGOTIATION, P.CONFIG_NEGOTIATION, P.CONFIG_LOCKED, P.READY)
TURN = (P.TURN_DECISION, P.COMMIT_SENT, P.ACKNOWLEDGED, P.REVEAL, P.VALIDATING)
ORDINARY = (*TURN, P.TURN_COMPLETE, P.SUBGAME_COMPLETE)
TECHNICAL = (*TURN, P.TECHNICAL_LOSS, P.SUBGAME_COMPLETE)


def _at(phase: ProtocolPhase, sub_game: int, series: SeriesConfig = SERIES) -> LocalOrchestrator:
    return LocalOrchestrator(ProtocolMachine(phase), series, sub_game)


def _walk(start: LocalOrchestrator, *targets: ProtocolPhase) -> tuple[LocalOrchestrator, list[int]]:
    cursors = [start.sub_game]
    current = start
    for target in targets:
        current = current.advance(target).orchestrator
        cursors.append(current.sub_game)
    return current, cursors


def test_ordinary_phase_transitions_never_move_the_cursor() -> None:
    final, cursors = _walk(LocalOrchestrator.start(SERIES), *TO_READY, *ORDINARY)
    assert final.machine.phase is P.SUBGAME_COMPLETE
    assert set(cursors) == {1}


def test_merely_entering_subgame_complete_does_not_increment() -> None:
    after = _at(P.TURN_COMPLETE, 3).advance(P.SUBGAME_COMPLETE).orchestrator
    assert after.machine.phase is P.SUBGAME_COMPLETE
    assert after.sub_game == 3


def test_the_next_sub_game_edge_increments_exactly_once() -> None:
    after = _at(P.SUBGAME_COMPLETE, 3).advance(P.READY).orchestrator
    assert after.machine.phase is P.READY
    assert after.sub_game == 4


def test_continuing_before_the_last_sub_game_is_allowed() -> None:
    for index in range(1, 6):
        assert _at(P.SUBGAME_COMPLETE, index).advance(P.READY).orchestrator.sub_game == index + 1


def test_the_last_sub_game_cannot_start_a_seventh() -> None:
    last = _at(P.SUBGAME_COMPLETE, 6)
    with pytest.raises(IllegalSubGameBranchError):
        last.advance(P.READY)
    assert last.sub_game == 6 and last.machine.phase is P.SUBGAME_COMPLETE


def test_the_series_cannot_end_before_every_sub_game_is_played() -> None:
    for index in range(1, 6):
        early = _at(P.SUBGAME_COMPLETE, index)
        with pytest.raises(IllegalSubGameBranchError):
            early.advance(P.SERIES_COMPLETE)
        assert early.sub_game == index


def test_the_last_sub_game_ends_the_series_without_moving_the_cursor() -> None:
    after = _at(P.SUBGAME_COMPLETE, 6).advance(P.SERIES_COMPLETE).orchestrator
    assert after.machine.phase is P.SERIES_COMPLETE
    assert after.sub_game == 6


def test_the_full_six_sub_game_series_makes_exactly_five_increments() -> None:
    current = LocalOrchestrator.start(SERIES)
    current, cursors = _walk(current, *TO_READY, *ORDINARY)
    for _ in range(5):
        current, more = _walk(current, P.READY, *ORDINARY)
        cursors += more[1:]
    assert cursors[-1] == 6
    increments = sum(1 for a, b in itertools.pairwise(cursors) if a != b)
    assert increments == 5
    current = current.advance(P.SERIES_COMPLETE).orchestrator
    assert current.machine.phase is P.SERIES_COMPLETE
    assert current.sub_game == 6


def test_a_middle_technical_loss_produces_the_same_cursor_sequence() -> None:
    def run(technical_at: int) -> list[int]:
        current = LocalOrchestrator.start(SERIES)
        current, cursors = _walk(current, *TO_READY)
        for index in range(1, 7):
            path = TECHNICAL if index == technical_at else ORDINARY
            current, more = _walk(current, *path)
            cursors += more[1:]
            if index < 6:
                current, more = _walk(current, P.READY)
                cursors += more[1:]
        return cursors

    assert run(3) == run(0)
    assert run(3)[-1] == 6


def test_a_technical_loss_cannot_skip_the_sub_game_boundary() -> None:
    lost = _at(P.TECHNICAL_LOSS, 2)
    for target in (P.READY, P.SERIES_COMPLETE, P.TURN_DECISION):
        with pytest.raises(Exception, match="illegal transition"):
            lost.advance(target)
    assert lost.sub_game == 2
    assert lost.advance(P.SUBGAME_COMPLETE).orchestrator.sub_game == 2


def test_no_seventh_sub_game_can_be_reached_by_any_route() -> None:
    """The series length is FIXED at 6, so a 7th sub-game has no representation."""
    with pytest.raises(InvalidSeriesError):
        SeriesConfig(num_games=7)
    with pytest.raises(IllegalSubGameBranchError):
        LocalOrchestrator(ProtocolMachine(P.READY), SERIES, 7)
    with pytest.raises(IllegalSubGameBranchError):
        _at(P.SUBGAME_COMPLETE, 6).advance(P.READY)
    reached = {
        _at(P.SUBGAME_COMPLETE, i).advance(P.READY).orchestrator.sub_game for i in range(1, 6)
    }
    assert reached == {2, 3, 4, 5, 6}


def test_a_technical_loss_on_the_last_sub_game_ends_the_series() -> None:
    current, _ = _walk(_at(P.TURN_DECISION, 6), *TECHNICAL[1:], P.SERIES_COMPLETE)
    assert current.machine.phase is P.SERIES_COMPLETE
    assert current.sub_game == 6
