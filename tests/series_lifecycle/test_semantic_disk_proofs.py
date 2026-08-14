"""The five capture routes, played by two real agents and read back off disk.

Each case runs one whole sub-game between two composed agents over the real
FastMCP transport, closes it through the production closure, and then opens the
official `log_<game_id>_g01.json` that was written. Nothing is asserted against
the runtime that produced the file - only against the bytes.

The thief plays no turn in these sub-games. That is deliberate: the questions
are all the police's, and a role that never moved still has a cell, which is
exactly what the replay reconstructs from the config it locked.
"""

import asyncio
import json
from pathlib import Path

import pytest
import r7_builders as r7
import test_two_agent_series as live
from r16_builders import GAME_ID, GROUP_A, GROUP_B

from mars777_police.app.artifact_store import log_name
from mars777_police.app.capture_values import CaptureAnswer, CaptureClaim
from mars777_police.app.protocol_values import FinalAuditVerdict
from mars777_police.app.sealed_record_values import ActorRole
from mars777_police.app.semantic_values import SemanticVerdict
from mars777_police.app.turn_cursor import TurnCursor
from mars777_police.domain.actions import BarrierAction, MoveAction
from mars777_police.domain.board import Position
from mars777_police.domain.rules import Move
from mars777_police.domain.terminal import Outcome
from mars777_police.series_runtime import SeriesRuntime

POLICE, THIEF = ActorRole.POLICE, ActorRole.THIEF
COP, HIDDEN = r7.CONFIG.board_and_agents.cop_start, r7.CONFIG.board_and_agents.thief_start
SOUTH = r7.ACTIONS[POLICE]
Step = tuple[object, CaptureClaim | None]


def steps_of(*steps: Step) -> tuple[Step, ...]:
    """The police's whole sub-game: one action, and one declaration or none."""
    return steps


TRAP = steps_of(
    (SOUTH, None),
    (BarrierAction(Position(1, 0)), None),
    (BarrierAction(COP), None),
)
"""Walk off the corner, then close both of the thief's ways out (GAME-005)."""


async def play(
    a: SeriesRuntime, b: SeriesRuntime, steps: tuple[Step, ...], legal: bool = True
) -> list[CaptureAnswer]:
    """One real sub-game of police turns, closed and written by production."""
    answers: list[CaptureAnswer] = []
    async with live.started(a, b):
        for series, group in ((a, GROUP_A), (b, GROUP_B)):
            r7.open_config(series, group, 1)
        r7.lock_round(a, b)
        for series in (a, b):
            series.lock_config(r7.CONFIG)
        a.open_sub_game(r7.evidence_for(POLICE, 1), r7.audit_for(THIEF, GROUP_B, 1))
        b.open_sub_game(r7.evidence_for(THIEF, 1), r7.audit_for(POLICE, GROUP_A, 1))
        cell, truth, walls = COP, None, ()
        for step, (action, claim) in enumerate(steps, start=1):
            cursor = TurnCursor(1, step)
            a.composition.runtime_context.bind_turn(
                r7.turn_for(POLICE, cursor, r7.own_truth(cell, walls))
            )
            b.composition.runtime_context.bind_turn(r7.turn_for(THIEF, cursor, truth))
            outcome = (
                await r7.one_turn(a, b, POLICE, cursor, action, claim, cell, walls)
                if legal
                else await r7.one_unvalidated_turn(a, b, POLICE, cursor, action, cell, walls)
            )
            answers.append(outcome.capture)
            cell, walls = r7.moved(cell, action), r7.placed(walls, action)
            truth = b.composition.runtime_context.current_turn().truth
            for series in (a, b):
                series.close_turn(series.composition.runtime_context.current_turn())
        for series in (a, b):
            await series.composition.peer_runner.send_final_nonce_reveal()
        for series in (a, b):
            await series.composition.peer_runner.send_audit_disclosure()
        for series in (a, b):
            series.close_sub_game(Outcome.CAPTURE)
    return answers


def run(root: Path, steps: tuple[Step, ...]) -> tuple[dict[str, object], list[CaptureAnswer]]:
    """Play the case and return the police's official log, read back from disk."""
    a, b = live.pair_for(root)
    answers = asyncio.run(play(a, b, steps))
    written = root / "police" / log_name(GAME_ID, 1)
    return json.loads(written.read_text(encoding="utf-8")), answers


def own_reveals(log: dict[str, object]) -> list[dict[str, object]]:
    """Every reveal the police wrote for itself, in step order."""
    entries = log["entries"]
    assert isinstance(entries, list)
    return [
        entry for entry in entries if entry["phase"] == "reveal" and entry["role"] == POLICE.value
    ]


def transcript(log: dict[str, object]) -> list[tuple[object, object]]:
    """The capture transcript exactly as the official file records it."""
    return [(one["capture_claim"], one["capture_answer"]) for one in own_reveals(log)]


def semantic(log: dict[str, object]) -> dict[str, object]:
    """The finding the replay wrote into the audit block."""
    audit = log["audit"]
    assert isinstance(audit, dict)
    found = audit["semantic"]
    assert isinstance(found, dict)
    return found


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
