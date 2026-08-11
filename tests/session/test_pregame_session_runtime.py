"""The pregame owner: real Step-0, real negotiation, real lock, real digest.

Stage 5-R3 stopped because nothing held this state. These tests drive the
production runtimes through it, so the identity it returns is the one a keyed
proof actually verified.
"""

import pytest
import session_builders as build
from peer_ops import lock_evidence, proposal, step0_exchange
from r16_builders import GROUP_A, GROUP_B

from mars777_police.app.protocol_errors import StaleMessageError


def test_step0_returns_the_identity_the_keyed_proof_verified() -> None:
    assert build.pregame().accept_step0(step0_exchange()) == GROUP_B


def test_step0_retains_the_merged_declaration_as_the_new_snapshot() -> None:
    """The merge `Step0Runtime` returns had no owner before this runtime."""
    runtime = build.pregame()
    before = runtime.declaration
    runtime.accept_step0(step0_exchange())
    assert runtime.declaration is not before
    assert runtime.declaration.teams.group_a is not None
    assert runtime.declaration.teams.group_b is not None


def test_a_second_step0_on_one_session_is_stale() -> None:
    runtime = build.pregame()
    runtime.accept_step0(step0_exchange())
    with pytest.raises(StaleMessageError, match="already completed Step-0"):
        runtime.accept_step0(step0_exchange())


def test_a_proposal_advances_the_round_state_the_runtime_owns() -> None:
    runtime = build.pregame()
    assert runtime.opening and runtime.seen == frozenset()
    assert runtime.accept_proposal(proposal(), GROUP_B) is True
    assert not runtime.opening
    assert runtime.seen == frozenset({GROUP_B})


def test_the_same_sender_cannot_propose_twice_in_one_round() -> None:
    runtime = build.pregame()
    runtime.accept_proposal(proposal(), GROUP_B)
    with pytest.raises(StaleMessageError, match="already proposed"):
        runtime.accept_proposal(proposal(), GROUP_B)


def test_a_non_participant_sender_is_refused() -> None:
    with pytest.raises(StaleMessageError, match="not a party"):
        build.pregame().accept_proposal(proposal(), "GROUP-INTRUDER")


def test_our_own_group_cannot_be_the_inbound_sender() -> None:
    with pytest.raises(StaleMessageError, match="from ourselves"):
        build.pregame().accept_proposal(proposal(), GROUP_A)


def test_lock_evidence_before_we_agreed_a_config_is_refused() -> None:
    """No local digest exists yet, and the peer's is never adopted instead."""
    with pytest.raises(StaleMessageError, match="before this side agreed"):
        build.pregame().accept_lock(lock_evidence())


def test_lock_evidence_verifies_against_our_own_registered_config() -> None:
    runtime = build.pregame()
    runtime.adopt_config(build.agreed())
    runtime.accept_lock(lock_evidence())
