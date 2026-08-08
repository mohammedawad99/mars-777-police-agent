"""The orchestrator asks; it never assumes (`STATE_MACHINE.md` §owner).

Phase legality has exactly one authority, `ProtocolMachine._ALLOWED`. The
orchestrator delegates every phase question to `ProtocolMachine.advance()` and
passes the emitted `TransitionEvidence` straight through - it never builds a
second one and never narrows or widens the frozen graph except through its own
sub-game cursor guard, which is a different question entirely.
"""

import ast
import itertools
import pathlib

import pytest

from mars777_police.app import orchestrator as orch
from mars777_police.app.orchestrator import (
    IllegalSubGameBranchError,
    LocalOrchestrator,
    OrchestratorResult,
)
from mars777_police.app.state_machine import (
    IllegalTransitionError,
    ProtocolMachine,
    ProtocolPhase,
    TransitionEvidence,
)
from mars777_police.domain.config_model import SeriesConfig

P = ProtocolPhase
SERIES = SeriesConfig()
LEGAL = [(s, t) for s in P for t in ProtocolMachine(s).allowed_next()]
CURSOR_EDGES = ((P.SUBGAME_COMPLETE, P.READY), (P.SUBGAME_COMPLETE, P.SERIES_COMPLETE))


def _at(phase: ProtocolPhase, sub_game: int = 1) -> LocalOrchestrator:
    return LocalOrchestrator(ProtocolMachine(phase), SERIES, sub_game)


def test_every_legal_edge_outside_the_cursor_branch_delegates_cleanly() -> None:
    checked = 0
    for source, target in LEGAL:
        if (source, target) in CURSOR_EDGES:
            continue
        before = _at(source)
        result = before.advance(target)
        assert isinstance(result, OrchestratorResult)
        assert result.orchestrator.machine.phase is target
        assert result.evidence == TransitionEvidence(source, target)
        assert before.machine.phase is source
        checked += 1
    assert checked == len(LEGAL) - 2 == 29


def test_the_evidence_is_exactly_the_machine_evidence() -> None:
    before = _at(P.VALIDATING)
    direct = before.machine.advance(P.TURN_COMPLETE).evidence
    assert before.advance(P.TURN_COMPLETE).evidence == direct


def test_the_orchestrator_never_constructs_transition_evidence() -> None:
    """Static proof of pass-through: the module makes no TransitionEvidence call."""
    tree = ast.parse(pathlib.Path(orch.__file__).read_text())
    calls = [
        n.func.id
        for n in ast.walk(tree)
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
    ]
    assert "TransitionEvidence" not in calls
    assert "TransitionResult" not in calls
    assert "ProtocolMachine" not in calls


def test_every_illegal_edge_is_refused_by_the_state_machine() -> None:
    refused = 0
    legal = set(LEGAL)
    for source, target in itertools.product(P, repeat=2):
        if (source, target) in legal:
            continue
        before = _at(source)
        with pytest.raises(IllegalTransitionError):
            before.advance(target)
        assert before.machine.phase is source
        assert before.sub_game == 1
        refused += 1
    assert refused == 293


def test_the_orchestrator_holds_no_second_transition_graph() -> None:
    tree = ast.parse(pathlib.Path(orch.__file__).read_text())
    assert sum(1 for n in ast.walk(tree) if isinstance(n, ast.Dict)) == 0
    for alias in ("ORCHESTRATOR_ALLOWED", "NEXT_PHASES", "TRANSITION_TABLE", "_ALLOWED"):
        assert not hasattr(orch, alias)


def test_a_rejected_transition_changes_nothing_at_all() -> None:
    before = _at(P.READY, 1)
    for bad in (P.REVEAL, P.SERIES_COMPLETE, P.BOOT, "READY", None):
        with pytest.raises((IllegalTransitionError, IllegalSubGameBranchError)):
            before.advance(bad)  # type: ignore[arg-type]
        assert before == _at(P.READY, 1)
        assert before.machine.phase is P.READY
        assert before.sub_game == 1


def test_equal_input_produces_equal_output() -> None:
    first = _at(P.READY).advance(P.TURN_DECISION)
    second = _at(P.READY).advance(P.TURN_DECISION)
    assert first == second
    assert first.evidence == second.evidence
    assert first.orchestrator == second.orchestrator


def test_the_orchestrator_imports_no_turn_service_or_outer_layer() -> None:
    tree = ast.parse(pathlib.Path(orch.__file__).read_text())
    modules = {n.module or "" for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}
    modules |= {a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
    for banned in ("turn_service", "protocol", "infra", "asyncio", "threading", "json"):
        assert not any(banned in m for m in modules), modules
