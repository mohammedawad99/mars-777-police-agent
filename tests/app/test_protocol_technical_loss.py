"""TECHNICAL_LOSS ends the current sub-game, not the machine (Stage 4A-FIX1).

`STATE_MACHINE.md` §4: the sub-game boundary already lists "technical loss" as
an entry condition and the phase is told to "proceed per series rules", while
R5 names only TAMPERED and FAILED as never returning to play. The single
corrected edge routes through SUBGAME_COMPLETE, which then branches to READY or
SERIES_COMPLETE.
"""

import pytest

from mars777_police.app.state_machine import (
    FAULT_PHASES,
    IllegalTransitionError,
    ProtocolMachine,
    ProtocolPhase,
)

P = ProtocolPhase


def test_technical_loss_is_a_fault_but_not_absorbing() -> None:
    # Fault identity and the graph property are independent: R5 names only
    # TAMPERED and FAILED as never returning to play.
    machine = ProtocolMachine(P.TECHNICAL_LOSS)
    assert P.TECHNICAL_LOSS in FAULT_PHASES
    assert not machine.is_absorbing
    assert machine.allowed_next() == (P.SUBGAME_COMPLETE,)


def test_technical_loss_permits_only_the_sub_game_boundary() -> None:
    machine = ProtocolMachine(P.TECHNICAL_LOSS)
    assert machine.advance(P.SUBGAME_COMPLETE).machine.phase is P.SUBGAME_COMPLETE
    for target in ProtocolPhase:
        if target is P.SUBGAME_COMPLETE:
            continue
        with pytest.raises(IllegalTransitionError):
            machine.advance(target)
        assert machine.phase is P.TECHNICAL_LOSS


def test_technical_loss_continues_into_the_next_sub_game() -> None:
    machine = ProtocolMachine(P.COMMIT_SENT).advance(P.TECHNICAL_LOSS).machine
    machine = machine.advance(P.SUBGAME_COMPLETE).machine
    assert machine.advance(P.READY).machine.phase is P.READY


def test_technical_loss_on_the_final_sub_game_reaches_the_report() -> None:
    machine = ProtocolMachine(P.VALIDATING).advance(P.TECHNICAL_LOSS).machine
    for phase in (P.SUBGAME_COMPLETE, P.SERIES_COMPLETE, P.FINAL_AUDIT, P.REPORT_READY):
        machine = machine.advance(phase).machine
    assert machine.phase is P.REPORT_READY
    assert machine.is_absorbing


def test_normal_play_is_reachable_again_after_a_technical_loss() -> None:
    seen, stack = {P.TECHNICAL_LOSS}, [P.TECHNICAL_LOSS]
    while stack:
        for target in ProtocolMachine(stack.pop()).allowed_next():
            if target not in seen:
                seen.add(target)
                stack.append(target)
    for phase in (
        P.SUBGAME_COMPLETE,
        P.READY,
        P.TURN_DECISION,
        P.SERIES_COMPLETE,
        P.FINAL_AUDIT,
        P.REPORT_READY,
    ):
        assert phase in seen
    assert P.BOOT not in seen
