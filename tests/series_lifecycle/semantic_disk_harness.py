"""Playing a real sub-game to disk, and reading back what it wrote.

Nothing here asserts. It plays a scripted sub-game through the production
runners, then offers the three views a proof needs: the steps taken, this side's
own reveals, and the semantic transcript the audit reads.
"""

import asyncio
import json
from pathlib import Path

import r7_builders as r7
import test_two_agent_series as live
from r16_builders import GAME_ID, GROUP_A, GROUP_B

from mars777_police.app.artifact_store import log_name
from mars777_police.app.capture_values import CaptureAnswer, CaptureClaim
from mars777_police.app.sealed_record_values import ActorRole
from mars777_police.app.turn_cursor import TurnCursor
from mars777_police.domain.terminal import Outcome
from mars777_police.series_runtime import SeriesRuntime

POLICE, THIEF = ActorRole.POLICE, ActorRole.THIEF
COP, HIDDEN = r7.CONFIG.board_and_agents.cop_start, r7.CONFIG.board_and_agents.thief_start
Step = tuple[object, CaptureClaim | None]
"""Walk off the corner, then close both of the thief's ways out (GAME-005)."""


def steps_of(*steps: Step) -> tuple[Step, ...]:
    """The police's whole sub-game: one action, and one declaration or none."""
    return steps


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
