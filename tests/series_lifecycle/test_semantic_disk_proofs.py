"""What a played sub-game leaves on disk, and how it replays from those bytes.

Each case plays a real turn and then reads the file back: an ordinary turn is a
question nobody asked, a true declaration replays as caught, a false one replays
as the claimant's own fault, and an illegal move is written as a technical loss
with the evidence that proves it.
"""

import asyncio
import json
from pathlib import Path

import pytest
import r7_builders as r7
import test_two_agent_series as live
from r16_builders import GAME_ID
from semantic_disk_harness import play, run, semantic, steps_of, transcript

from mars777_police.app.artifact_store import log_name
from mars777_police.app.capture_values import CaptureAnswer, CaptureClaim
from mars777_police.app.protocol_values import FinalAuditVerdict
from mars777_police.app.sealed_record_values import ActorRole
from mars777_police.app.semantic_values import SemanticVerdict
from mars777_police.domain.actions import BarrierAction, MoveAction
from mars777_police.domain.board import Position
from mars777_police.domain.rules import Move
from mars777_police.domain.terminal import Outcome

POLICE, THIEF = ActorRole.POLICE, ActorRole.THIEF
COP, HIDDEN = r7.CONFIG.board_and_agents.cop_start, r7.CONFIG.board_and_agents.thief_start
SOUTH = r7.ACTIONS[POLICE]
Step = tuple[object, CaptureClaim | None]
TRAP = steps_of(
    (SOUTH, None),
    (BarrierAction(Position(1, 0)), None),
    (BarrierAction(COP), None),
)
"""Walk off the corner, then close both of the thief's ways out (GAME-005)."""


def test_an_ordinary_turn_is_written_as_a_question_nobody_asked(tmp_path: Path) -> None:
    log, answers = run(tmp_path, steps_of((SOUTH, None)))
    assert answers == [CaptureAnswer.NO_QUESTION]
    assert transcript(log) == [(None, "NO_QUESTION")]
    assert semantic(log)["verdict"] == SemanticVerdict.CONSISTENT.value


def test_a_true_declaration_is_written_as_caught_and_replays_as_true(tmp_path: Path) -> None:
    log, answers = run(tmp_path, steps_of((SOUTH, CaptureClaim(HIDDEN))))
    assert answers == [CaptureAnswer.CAUGHT]
    assert transcript(log) == [([HIDDEN.row, HIDDEN.col], "CAUGHT")]
    assert semantic(log)["verdict"] == SemanticVerdict.CONSISTENT.value


def test_a_false_declaration_is_written_and_replays_as_the_claimant_s_fault(
    tmp_path: Path,
) -> None:
    away = Position(6, 6)
    log, answers = run(tmp_path, steps_of((SOUTH, CaptureClaim(away))))
    assert answers == [CaptureAnswer.NOT_CAUGHT]
    assert transcript(log) == [([away.row, away.col], "NOT_CAUGHT")]
    assert semantic(log) == {
        "verdict": SemanticVerdict.FALSE_CAPTURE_CLAIM.value,
        "step": 1,
        "at_fault": POLICE.value,
        "also_at_fault": None,
    }


def test_a_barrier_on_the_thief_cell_is_written_as_caught(tmp_path: Path) -> None:
    log, answers = run(tmp_path, steps_of((BarrierAction(HIDDEN), None)))
    assert answers == [CaptureAnswer.CAUGHT]
    assert transcript(log) == [(None, "CAUGHT")]
    assert semantic(log)["verdict"] == SemanticVerdict.CONSISTENT.value


def test_the_barrier_that_closes_the_last_way_out_is_written_as_caught(tmp_path: Path) -> None:
    log, answers = run(tmp_path, TRAP)
    assert answers == [CaptureAnswer.NO_QUESTION] * 2 + [CaptureAnswer.CAUGHT]
    assert transcript(log) == [(None, "NO_QUESTION"), (None, "NO_QUESTION"), (None, "CAUGHT")]
    assert semantic(log)["verdict"] == SemanticVerdict.CONSISTENT.value


def test_an_illegal_move_is_written_as_a_technical_loss_with_verified_evidence(
    tmp_path: Path,
) -> None:
    """North from row 0 leaves the board: honest record, illegal game action.

    Sent through the unvalidated-peer harness, because a production sender now
    refuses its own illegal action before sealing anything - which is exactly
    why the semantic audit has to keep working against a peer that does not.
    """
    a, b = live.pair_for(tmp_path)
    asyncio.run(play(a, b, steps_of((MoveAction(Move.N), None)), legal=False))
    log = json.loads((tmp_path / "police" / log_name(GAME_ID, 1)).read_text(encoding="utf-8"))
    audit = log["audit"]
    (line,) = a.lines

    assert COP.row == 0, "the police starts on the top row"
    assert audit["result"] == FinalAuditVerdict.VERIFIED_OK.value, "no hash or transcript fault"
    assert audit["tampered_step"] is None
    assert audit["semantic"]["verdict"] == SemanticVerdict.ILLEGAL_ACTION.value
    assert audit["semantic"]["at_fault"] == POLICE.value
    assert line.outcome is Outcome.TECHNICAL_LOSS
    assert (line.cop_score, line.thief_score) == (0, 0)


@pytest.mark.parametrize(
    ("steps", "expected"),
    [
        (steps_of((SOUTH, None)), Outcome.CAPTURE),
        (steps_of((SOUTH, CaptureClaim(Position(6, 6)))), Outcome.TECHNICAL_LOSS),
    ],
)
def test_only_the_false_declaration_is_scored_as_a_technical_loss(
    tmp_path: Path, steps: tuple[Step, ...], expected: Outcome
) -> None:
    a, b = live.pair_for(tmp_path)
    asyncio.run(play(a, b, steps))
    (line,) = a.lines
    assert line.outcome is expected
    lost = expected is Outcome.TECHNICAL_LOSS
    assert (line.cop_score, line.thief_score) == ((0, 0) if lost else (20, 5))
