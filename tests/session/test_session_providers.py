"""Lifecycle-scoped runtimes are resolved per call, never captured once.

`TurnProtocolRuntime` is terminal at `CONSUMED` and `AuditRuntime` at
`COMPLETE`. An adapter that stored the first one it saw would spend the rest of
the game talking to a corpse, so these tests hand the providers a *different*
runtime on the second call and require the adapter to follow.
"""

import audit_builders
import pytest
import session_builders as build
import turn_builders

from mars777_police.app.protocol_errors import StaleMessageError
from mars777_police.app.turn_protocol_state import TurnPhase
from mars777_police.transport.peer_operations import InboundPeerOperations


def rotating(values: list[object]) -> object:
    """A provider that yields the next runtime on every resolution."""
    calls = iter(values)
    return lambda: next(calls)


def test_a_consumed_turn_runtime_is_not_cached_across_operations() -> None:
    first, second = turn_builders.runtime(), turn_builders.runtime()
    adapter = InboundPeerOperations(
        build.pregame(), rotating([first, second]), audit_builders.runtime, build.exchange
    )
    adapter.on_commitment(turn_builders.commitment(), build.bound())
    adapter.on_commitment(turn_builders.commitment(), build.bound())
    assert first.phase is TurnPhase.AWAITING_OUR_ACKNOWLEDGEMENT
    assert second.phase is TurnPhase.AWAITING_OUR_ACKNOWLEDGEMENT
    assert first is not second


def test_a_completed_audit_runtime_is_not_cached_across_operations() -> None:
    """The disclosure reaches whatever the provider returns *now*, not before.

    The second runtime is still `AWAITING_NONCES`, so it refuses - which is the
    proof: an adapter holding the first one would have completed the audit.
    """
    first, second = audit_builders.runtime(), audit_builders.runtime()
    adapter = InboundPeerOperations(
        build.pregame(), turn_builders.runtime, rotating([first, second]), build.exchange
    )
    session = build.bound(audit_builders.PEER_GROUP)
    adapter.on_final_nonce_reveal(audit_builders.nonce_batch(), session)
    with pytest.raises(StaleMessageError, match="cannot arrive"):
        adapter.on_audit_disclosure(audit_builders.document(), session)
    assert first.verdict is None and second.verdict is None


def test_the_adapter_stores_only_injected_dependencies() -> None:
    """No cursor, phase, digest, verdict or sender lives on the adapter."""
    from dataclasses import fields

    assert {f.name for f in fields(InboundPeerOperations)} == {
        "pregame",
        "turns",
        "audits",
        "results",
    }
    assert InboundPeerOperations.__dataclass_params__.frozen


def test_a_second_audit_resolution_reaches_the_second_runtime() -> None:
    first, second = audit_builders.runtime(), audit_builders.runtime()
    adapter = InboundPeerOperations(
        build.pregame(), turn_builders.runtime, rotating([first, second]), build.exchange
    )
    session = build.bound(audit_builders.PEER_GROUP)
    adapter.on_final_nonce_reveal(audit_builders.nonce_batch(), session)
    adapter.on_final_nonce_reveal(audit_builders.nonce_batch(), session)
    assert first.phase.value == "AWAITING_DISCLOSURE"
    assert second.phase.value == "AWAITING_DISCLOSURE"
