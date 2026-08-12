"""Four typed slots, four refusals, and one result that binds exactly once."""

import audit_builders
import composed_builders as build
import pytest
import turn_builders
from evidence_builders import producer

from mars777_police.app.active_runtime_context import ActiveRuntimeContext
from mars777_police.app.protocol_errors import LocalDefectError, StaleMessageError
from mars777_police.app.turn_cursor import TurnCursor


def test_every_slot_starts_unbound() -> None:
    context = ActiveRuntimeContext()
    assert (context.turn, context.evidence, context.audit, context.result) == (None,) * 4


@pytest.mark.parametrize(
    ("accessor", "message"),
    [
        ("current_turn", "no turn is active"),
        ("current_evidence", "no sub-game is active"),
        ("current_audit", "no sub-game is active"),
        ("current_result", "not available yet"),
    ],
)
def test_an_unbound_slot_refuses_rather_than_returning_none(accessor: str, message: str) -> None:
    with pytest.raises(StaleMessageError, match=message):
        getattr(ActiveRuntimeContext(), accessor)()


def test_the_context_declares_exactly_four_named_runtime_slots() -> None:
    """Typed slots, not a registry: no string key can reach anything here."""
    import dataclasses

    assert {f.name for f in dataclasses.fields(ActiveRuntimeContext)} == {
        "turn",
        "evidence",
        "audit",
        "result",
    }
    for generic in ("get", "set", "register", "lookup", "resolve"):
        assert not hasattr(ActiveRuntimeContext, generic)


def test_binding_a_sub_game_makes_both_owners_current() -> None:
    context = ActiveRuntimeContext()
    evidence, audit = producer(), audit_builders.runtime()
    context.bind_sub_game(evidence, audit)
    assert context.current_evidence() is evidence
    assert context.current_audit() is audit


def test_a_sub_game_whose_owners_disagree_is_refused_atomically() -> None:
    context = ActiveRuntimeContext()
    first, audit = producer(), audit_builders.runtime()
    context.bind_sub_game(first, audit)
    from series_builders import audit_of

    with pytest.raises(LocalDefectError, match="one identity"):
        context.bind_sub_game(first, audit_of(2))
    assert context.current_evidence() is first and context.current_audit() is audit


def test_binding_a_turn_replaces_only_the_turn() -> None:
    context = ActiveRuntimeContext()
    evidence, audit = producer(), audit_builders.runtime()
    context.bind_sub_game(evidence, audit)
    turn = turn_builders.runtime()
    context.bind_turn(turn)
    assert context.current_turn() is turn
    assert context.current_evidence() is evidence and context.current_audit() is audit


def test_a_turn_from_another_sub_game_is_refused() -> None:
    """`TurnCursor` already carries the sub-game, so nothing was invented."""
    context = ActiveRuntimeContext()
    context.bind_sub_game(producer(), audit_builders.runtime())
    stray = turn_builders.runtime()
    stray.cursor = TurnCursor(2, 1)
    with pytest.raises(LocalDefectError, match="not the active"):
        context.bind_turn(stray)


def test_a_turn_may_be_bound_before_any_sub_game() -> None:
    context = ActiveRuntimeContext()
    turn = turn_builders.runtime()
    context.bind_turn(turn)
    assert context.current_turn() is turn


def test_the_result_binds_once_for_the_series() -> None:
    """A second, different answer to what the series produced is refused."""
    composition = build.after_step0(build.compose())
    exchange = composition.complete_result(**build.final_result_inputs())
    assert composition.runtime_context.current_result() is exchange
    with pytest.raises(LocalDefectError, match="already has a result"):
        composition.runtime_context.bind_result(exchange)
