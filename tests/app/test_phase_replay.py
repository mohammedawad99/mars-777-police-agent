"""Structural phase-path replay from an ordered evidence sequence.

This proves only that the ordered PROTOCOL PHASE PATH can be reconstructed.
It is **not** complete game replay: positions, effects, scores, commitment and
nonce verification, and the official artifacts are all owned elsewhere. No
cryptography is involved, so the check below detects structural corruption
only, never forgery.
"""

import os
import subprocess
import sys
from collections.abc import Sequence

import pytest

from mars777_police.app.state_machine import (
    IllegalTransitionError,
    ProtocolMachine,
    ProtocolPhase,
    TransitionEvidence,
)

P = ProtocolPhase
TURN = (P.COMMIT_SENT, P.ACKNOWLEDGED, P.REVEAL, P.VALIDATING, P.TURN_COMPLETE)
TO_READY = (P.STEP0_NEGOTIATION, P.CONFIG_NEGOTIATION, P.CONFIG_LOCKED, P.READY)
AUDIT = (P.SERIES_COMPLETE, P.FINAL_AUDIT, P.REPORT_READY)
PROBE = (
    "from mars777_police.app.state_machine import ProtocolMachine, ProtocolPhase as P;"
    "r=ProtocolMachine.start().advance(P.STEP0_NEGOTIATION);"
    "print(r.evidence.source_phase.value, r.evidence.target_phase.value, r.machine.phase.value)"
)


def _run(*targets: ProtocolPhase) -> tuple[ProtocolMachine, list[TransitionEvidence]]:
    machine, trail = ProtocolMachine.start(), []
    for target in targets:
        result = machine.advance(target)
        machine, _ = result.machine, trail.append(result.evidence)
    return machine, trail


def _replay(trail: Sequence[TransitionEvidence], start: ProtocolPhase = P.BOOT) -> ProtocolPhase:
    """Reconstruct the phase path, rejecting any break in the chain.

    Only the chain needs checking: every record is a legal edge by construction
    (Stage 4B-FIX1), so a chained source implies a real walk of the graph.
    """
    expected = start
    for evidence in trail:
        if evidence.source_phase is not expected:
            raise ValueError(f"chain break at {evidence.source_phase.value}")
        expected = evidence.target_phase
    return expected


def test_boot_to_first_turn_replays() -> None:
    machine, trail = _run(*TO_READY, P.TURN_DECISION)
    assert len(trail) == 5
    assert _replay(trail) is machine.phase is P.TURN_DECISION


def test_a_full_turn_loop_replays() -> None:
    machine, trail = _run(*TO_READY, P.TURN_DECISION, *TURN, P.TURN_DECISION)
    assert _replay(trail) is machine.phase is P.TURN_DECISION


def test_sub_game_continuation_replays() -> None:
    machine, trail = _run(*TO_READY, P.TURN_DECISION, *TURN, P.SUBGAME_COMPLETE, P.READY)
    assert _replay(trail) is machine.phase is P.READY


def test_series_completion_replays() -> None:
    machine, trail = _run(*TO_READY, P.TURN_DECISION, *TURN, P.SUBGAME_COMPLETE, *AUDIT)
    assert _replay(trail) is machine.phase is P.REPORT_READY


def test_technical_loss_continuation_replays() -> None:
    # Technical loss straight out of COMMIT_SENT, then the next sub-game.
    steps = (P.TURN_DECISION, P.COMMIT_SENT, P.TECHNICAL_LOSS, P.SUBGAME_COMPLETE, P.READY)
    machine, trail = _run(*TO_READY, *steps)
    assert _replay(trail) is machine.phase is P.READY


def test_final_technical_loss_series_path_replays() -> None:
    # A full commit/reveal turn that ends in technical loss, then the audit.
    steps = (P.TURN_DECISION, *TURN[:4], P.TECHNICAL_LOSS, P.SUBGAME_COMPLETE, *AUDIT)
    machine, trail = _run(*TO_READY, *steps)
    assert _replay(trail) is machine.phase is P.REPORT_READY


def test_a_wrong_source_phase_is_detected() -> None:
    _, trail = _run(*TO_READY)
    broken = [TransitionEvidence(P.READY, P.TURN_DECISION), *trail[1:]]
    with pytest.raises(ValueError, match="chain break"):
        _replay(broken)


def test_swapped_order_is_detected() -> None:
    _, trail = _run(*TO_READY)
    swapped = [trail[1], trail[0], *trail[2:]]
    with pytest.raises(ValueError, match="chain break"):
        _replay(swapped)


def test_a_missing_middle_transition_is_detected() -> None:
    _, trail = _run(*TO_READY)
    with pytest.raises(ValueError, match="chain break"):
        _replay([trail[0], trail[2], trail[3]])


def test_a_duplicated_record_is_detected() -> None:
    _, trail = _run(*TO_READY)
    with pytest.raises(ValueError, match="chain break"):
        _replay([trail[0], trail[0], *trail[1:]])


def test_a_valid_record_replayed_out_of_position_is_detected() -> None:
    _, trail = _run(*TO_READY)
    with pytest.raises(ValueError, match="chain break"):
        _replay([*trail, trail[2]])


def test_an_impossible_pair_cannot_reach_replay_at_all() -> None:
    """The corruption boundary moved forward: it is now the constructor.

    No such record can enter a trail, no constructor was weakened to make one,
    and no bypass (``object.__new__``, patching) is used to fabricate it.
    """
    with pytest.raises(IllegalTransitionError, match="illegal transition BOOT -> REVEAL"):
        TransitionEvidence(P.BOOT, P.REVEAL)
    assert _replay([]) is P.BOOT


def test_replay_is_stable_under_python_hash_randomisation() -> None:
    outputs = set()
    for seed in ("0", "1", "424242"):
        run = subprocess.run(
            [sys.executable, "-c", PROBE],
            capture_output=True,
            text=True,
            env=dict(os.environ, PYTHONHASHSEED=seed),
            check=True,
        )
        outputs.add(run.stdout.strip())
    assert len(outputs) == 1
