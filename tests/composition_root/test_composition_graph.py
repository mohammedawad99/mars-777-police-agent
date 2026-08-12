"""What the composition root builds, shares, and deliberately does not do."""

import dataclasses

import composed_builders as build
import pytest
from r16_builders import GROUP_A, GROUP_B

from mars777_police.app.protocol_errors import StaleMessageError
from mars777_police.composition import compose_agent
from mars777_police.composition_values import AgentComposition, SeriesIdentity
from mars777_police.transport.server import PEER_TOOLS


def test_the_composition_exposes_only_what_boot_needs() -> None:
    assert {f.name for f in dataclasses.fields(AgentComposition)} == {
        "server",
        "peer_client",
        "peer_transport",
        "peer_runner",
        "inbound_operations",
        "pregame",
        "runtime_context",
        "series_audit",
        "identity",
        "group_id",
        "clock",
        "digester",
    }
    assert AgentComposition.__dataclass_params__.frozen


def test_construction_starts_nothing() -> None:
    """No session entered, no socket bound, no traffic - objects only."""
    composition = build.compose()
    assert composition.peer_client._session is None
    assert composition.peer_client._stack is None
    assert sorted(PEER_TOOLS) == ["negotiate", "receive_control", "receive_turn", "submit_audit"]


def test_the_result_owner_is_absent_at_startup() -> None:
    """Nothing truthful exists to build it from before the series is played."""
    composition = build.compose()
    assert composition.runtime_context.result is None
    with pytest.raises(StaleMessageError, match="not available yet"):
        composition.runtime_context.current_result()


def test_the_pregame_owner_is_shared_by_both_paths() -> None:
    composition = build.compose()
    assert composition.peer_runner.pregame is composition.inbound_operations.pregame
    assert composition.peer_runner.pregame is composition.pregame


def test_the_series_audit_gate_is_one_object() -> None:
    composition = build.compose()
    assert composition.peer_runner.series is composition.series_audit


def test_the_transport_is_one_object_shared_with_the_late_result() -> None:
    composition = build.after_step0(build.compose())
    assert composition.peer_runner.transport is composition.peer_transport
    exchange = composition.complete_result(**build.final_result_inputs())
    assert exchange.transport is composition.peer_transport


def test_both_paths_resolve_the_same_current_runtimes() -> None:
    """One `ActiveRuntimeContext` feeds the inbound adapter and the runner."""
    import audit_builders
    import turn_builders
    from evidence_builders import producer

    composition = build.compose()
    context = composition.runtime_context
    turn, evidence, audit = turn_builders.runtime(), producer(), audit_builders.runtime()
    context.bind_sub_game(evidence, audit)
    context.bind_turn(turn)
    assert composition.peer_runner.turns() is composition.inbound_operations.turns() is turn
    assert composition.peer_runner.evidence() is evidence
    assert composition.inbound_operations.audits() is audit


def test_a_new_sub_game_switches_both_paths() -> None:
    """Neither adapter caches g01 once g02 is bound."""
    import series_builders
    from evidence_builders import producer

    composition = build.compose()
    context = composition.runtime_context
    first_evidence, first_audit = producer(), series_builders.audit_of(1)
    context.bind_sub_game(first_evidence, first_audit)
    assert composition.peer_runner.evidence() is first_evidence
    second_evidence, second_audit = producer(), series_builders.audit_of(1)
    context.bind_sub_game(second_evidence, second_audit)
    assert composition.peer_runner.evidence() is second_evidence
    assert composition.inbound_operations.audits() is second_audit


def test_the_first_config_round_is_the_one_it_was_told() -> None:
    composition = build.compose()
    assert composition.pregame.negotiation.sub_game == build.FIRST_SUB_GAME
    assert composition.pregame.lock.sub_game == build.FIRST_SUB_GAME
    assert composition.identity.first_sub_game == build.FIRST_SUB_GAME


def test_the_series_identity_refuses_an_impossible_value() -> None:
    identity = build.identity_for(GROUP_A, "group_a")
    with pytest.raises(ValueError, match="non-empty"):
        dataclasses.replace(identity, game_id="")
    with pytest.raises(ValueError, match="positive int"):
        dataclasses.replace(identity, first_sub_game=0)


def test_a_missing_opponent_endpoint_refuses_composition() -> None:
    """No localhost fallback and no discovery: it is configured or it is absent."""
    from mars777_police.app.sealed_record_values import ActorRole

    settings = dataclasses.replace(
        build.settings_for(ActorRole.POLICE, "https://x.example/mcp"), opponent=None
    )
    with pytest.raises(ValueError, match="opponent public endpoint"):
        compose_agent(settings, build.identity_for(GROUP_A, "group_a"), GROUP_A)


def test_two_compositions_share_nothing() -> None:
    a, b = build.both("http://127.0.0.1:1/mcp", "http://127.0.0.1:2/mcp")
    for name in ("server", "peer_client", "peer_transport", "pregame", "runtime_context"):
        assert getattr(a, name) is not getattr(b, name)
    assert a.series_audit is not b.series_audit
    import turn_builders

    a.runtime_context.bind_turn(turn_builders.runtime())
    assert b.runtime_context.turn is None


def test_reconstruction_from_the_same_settings_leaks_nothing() -> None:
    first = build.after_step0(build.compose())
    from r16_builders import config

    first.pregame.adopt_config(config())
    second = build.compose()
    assert second.pregame.peer is None
    assert second.pregame.opening and second.pregame.seen == frozenset()
    assert second.pregame.config is None
    assert second.runtime_context.result is None
    assert isinstance(second.identity, SeriesIdentity)
    assert second.group_id == GROUP_A != GROUP_B
