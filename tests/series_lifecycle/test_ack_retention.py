"""Acknowledgement retention: one event per validated acknowledgement, never more.

The wire message is untouched - these prove that the *runtime* keeps what the
official log needs, and that a refused acknowledgement leaves nothing behind.
"""

import pytest
import turn_builders
from r16_builders import GROUP_B

from mars777_police.app.peer_turn_messages import Acknowledgement
from mars777_police.app.protocol_errors import StaleMessageError
from mars777_police.app.protocol_values import Sha256Digest
from mars777_police.app.sealed_record_values import ActorRole
from mars777_police.app.turn_protocol_state import AckEvidence, TurnPhase


def test_an_outbound_acknowledgement_is_retained_once_with_our_role() -> None:
    runtime = turn_builders.runtime(ActorRole.POLICE)
    runtime.accept_commitment(turn_builders.commitment())
    acknowledgement = runtime.acknowledge()
    assert runtime.acks == (
        AckEvidence(acknowledgement.cursor, acknowledgement.h_commit, ActorRole.POLICE),
    )


def test_an_inbound_acknowledgement_is_retained_once_with_the_peer_role() -> None:
    runtime = turn_builders.runtime(ActorRole.POLICE)
    runtime.register_local_commitment(turn_builders.commitment(digest=turn_builders.OUR_DIGEST))
    runtime.accept_acknowledgement(turn_builders.acknowledgement(digest=turn_builders.OUR_DIGEST))
    assert runtime.acks == (
        AckEvidence(turn_builders.START, turn_builders.OUR_DIGEST, ActorRole.THIEF),
    )
    with pytest.raises(StaleMessageError, match="already acknowledged"):
        runtime.accept_acknowledgement(
            turn_builders.acknowledgement(digest=turn_builders.OUR_DIGEST)
        )
    assert len(runtime.acks) == 1


def test_a_refused_acknowledgement_leaves_no_event_behind() -> None:
    runtime = turn_builders.runtime(ActorRole.THIEF)
    with pytest.raises(StaleMessageError, match="no commitment of ours"):
        runtime.accept_acknowledgement(turn_builders.acknowledgement())
    runtime.register_local_commitment(turn_builders.commitment(digest=turn_builders.OUR_DIGEST))
    with pytest.raises(StaleMessageError, match="committed digest"):
        runtime.accept_acknowledgement(turn_builders.acknowledgement(digest=Sha256Digest("f" * 64)))
    with pytest.raises(StaleMessageError, match="nothing to acknowledge"):
        runtime.acknowledge()
    assert runtime.acks == ()


def test_the_acknowledgement_wire_value_gained_no_field() -> None:
    """Retention is local: the peer message is still exactly cursor + digest."""
    from dataclasses import fields

    assert {field.name for field in fields(Acknowledgement)} == {"cursor", "h_commit"}
    assert runtime_phase_unchanged()


def runtime_phase_unchanged() -> bool:
    """Acknowledging still moves the phase exactly as the frozen cadence says."""
    runtime = turn_builders.runtime(ActorRole.POLICE)
    runtime.accept_commitment(turn_builders.commitment())
    runtime.acknowledge()
    return runtime.phase is TurnPhase.AWAITING_REVEAL and runtime.peer_role is ActorRole.THIEF


def test_the_peer_role_is_the_complement_of_our_locked_role() -> None:
    assert turn_builders.runtime(ActorRole.THIEF).peer_role is ActorRole.POLICE
    assert GROUP_B  # the peer group is a session fact, never the role source
