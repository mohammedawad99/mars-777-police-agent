"""All nine operations, each reaching its real production owner.

No spy stands in for an application here: the runtimes are the production
classes, so an assertion below fails if the adapter delegated to the wrong one
or quietly did the work itself.
"""

import audit_builders
import pytest
import session_builders as build
import turn_builders
from peer_ops import agreement, audit_document, lock_evidence, proposal, step0_exchange
from r16_builders import GROUP_B

from mars777_police.app.protocol_errors import MalformedMessageError, StaleMessageError
from mars777_police.app.protocol_values import FinalAuditVerdict
from mars777_police.app.turn_protocol_state import TurnPhase


def test_step0_binds_the_identity_the_application_verified() -> None:
    session = build.unbound()
    build.operations().on_step0(step0_exchange(), session)
    assert session.require_peer() == GROUP_B


def test_a_failed_step0_leaves_the_session_unbound() -> None:
    """Transactional: the binding happens only after the application succeeded."""
    runtime = build.pregame()
    runtime.accept_step0(step0_exchange())
    session = build.unbound()
    with pytest.raises(StaleMessageError):
        build.operations(session_runtime=runtime).on_step0(step0_exchange(), session)
    assert not session.is_authenticated and session.pending is None


def test_config_proposal_reaches_the_real_negotiation_runtime() -> None:
    runtime = build.pregame()
    build.operations(session_runtime=runtime).on_config_proposal(proposal(), build.bound())
    assert runtime.seen == frozenset({GROUP_B}) and not runtime.opening


def test_config_lock_reaches_the_real_lock_runtime() -> None:
    runtime = build.pregame()
    runtime.adopt_config(build.agreed())
    build.operations(session_runtime=runtime).on_config_lock(lock_evidence(), build.bound())


def test_the_turn_trio_drives_one_real_turn_protocol_runtime() -> None:
    turn = turn_builders.runtime()
    live = build.operations(turn=turn)
    live.on_commitment(turn_builders.commitment(), build.bound())
    assert turn.phase is TurnPhase.AWAITING_OUR_ACKNOWLEDGEMENT
    turn.acknowledge()
    assert live.on_reveal(turn_builders.legal_reveal(), build.bound()) is True
    assert turn.phase is TurnPhase.CONSUMED


def test_acknowledgement_reaches_the_real_turn_runtime() -> None:
    turn = turn_builders.runtime()
    turn.register_local_commitment(turn_builders.commitment(digest=turn_builders.OUR_DIGEST))
    build.operations(turn=turn).on_acknowledgement(
        turn_builders.acknowledgement(digest=turn_builders.OUR_DIGEST), build.bound()
    )
    assert turn.local_acknowledged


def test_an_illegal_reveal_returns_false_rather_than_raising() -> None:
    turn = turn_builders.runtime()
    live = build.operations(turn=turn)
    live.on_commitment(turn_builders.commitment(), build.bound())
    turn.acknowledge()
    assert live.on_reveal(turn_builders.illegal_reveal(), build.bound()) is False


def test_a_protocol_invalid_reveal_raises_and_is_never_false() -> None:
    """`False` keeps its one meaning: an out-of-order reveal is a typed failure."""
    with pytest.raises(StaleMessageError):
        build.operations().on_reveal(turn_builders.legal_reveal(), build.bound())


def test_the_audit_pair_drives_one_real_audit_runtime_to_a_verdict() -> None:
    audit = audit_builders.runtime()
    live = build.operations(audit=audit)
    live.on_final_nonce_reveal(audit_builders.nonce_batch(), build.bound(audit_builders.PEER_GROUP))
    live.on_audit_disclosure(audit_builders.document(), build.bound(audit_builders.PEER_GROUP))
    assert audit.verdict is FinalAuditVerdict.VERIFIED_OK


def test_audit_disclosure_reaches_the_runtime_unparsed() -> None:
    """The adapter reads nothing: the refusal comes from the runtime's reader."""
    audit = audit_builders.runtime()
    live = build.operations(audit=audit)
    live.on_final_nonce_reveal(audit_builders.nonce_batch(), build.bound(audit_builders.PEER_GROUP))
    with pytest.raises(MalformedMessageError, match="audit disclosure"):
        live.on_audit_disclosure(audit_document(), build.bound(audit_builders.PEER_GROUP))


def test_result_agreement_returns_the_production_digest() -> None:
    live = build.exchange()
    from mars777_police.transport.peer_operations import InboundPeerOperations

    adapter = InboundPeerOperations(
        build.pregame(), turn_builders.runtime, audit_builders.runtime, live
    )
    digest = adapter.on_result_agreement(agreement(), build.bound(GROUP_B))
    assert digest is live.local_digest and live.peer_request_handled
