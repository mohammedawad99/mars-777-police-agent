"""Config lock: symmetric evidence, and a gate that refuses on any single failure.

Nothing the peer sends is taken on trust. Its digest is compared against our own
recomputation and its profiles member-for-member, and the proof is verified
*before* the digest so an unauthenticated core is never even compared.
"""

from dataclasses import replace

import pytest
from r16_builders import GAME_ID, GAME_UID, KEY_ID, PROFILES, SHARED_KEY, config

from mars777_police.app.auth_values import AuthProfile, AuthProof
from mars777_police.app.config_lock_runtime import ConfigLockGate, ConfigLockRuntime
from mars777_police.app.interop_profiles import SeriesConvention
from mars777_police.app.peer_pregame_messages import ConfigLockEvidence
from mars777_police.app.protocol_errors import (
    AuthFailureError,
    ConfigMismatchError,
    ConventionMismatchError,
    StaleMessageError,
)
from mars777_police.app.protocol_values import Sha256Digest
from mars777_police.app.state_machine import ProtocolMachine, ProtocolPhase
from mars777_police.domain.config_sections import WorldTerms
from mars777_police.protocol.config_lock import ConfigLockAuthenticator
from mars777_police.protocol.keyed_auth import HmacSha256Provider, KeyedAuthenticator


def adapter() -> ConfigLockAuthenticator:
    return ConfigLockAuthenticator(
        KeyedAuthenticator(
            AuthProfile.HMAC_SHA256, KEY_ID, HmacSha256Provider({KEY_ID.value: SHARED_KEY})
        )
    )


def runtime(sub_game: int = 1, profiles: object = PROFILES) -> ConfigLockRuntime:
    shared = adapter()
    return ConfigLockRuntime(GAME_ID, GAME_UID, sub_game, profiles, shared, shared)


def test_both_peers_produce_identical_evidence_from_the_same_config() -> None:
    ours, theirs = runtime().outbound(config()), runtime().outbound(config())
    assert ours == theirs
    assert ours.context.config_sha256 == adapter().digest(config())


def test_valid_peer_evidence_verifies_against_our_own_recomputation() -> None:
    digest = adapter().digest(config())
    runtime().accept(runtime().outbound(config()), digest)


def test_a_peer_digest_that_differs_from_our_recomputation_is_refused() -> None:
    other = replace(config(), world=WorldTerms("New York", 16))
    with pytest.raises(ConfigMismatchError):
        runtime().accept(runtime().outbound(other), adapter().digest(config()))


def test_a_wrong_sub_game_is_stale() -> None:
    with pytest.raises(StaleMessageError):
        runtime(1).accept(runtime(2).outbound(config()), adapter().digest(config()))


def test_evidence_for_another_game_is_stale() -> None:
    shared = adapter()
    other = ConfigLockRuntime("another-game", GAME_UID, 1, PROFILES, shared, shared)
    with pytest.raises(StaleMessageError):
        runtime().accept(other.outbound(config()), adapter().digest(config()))


def test_a_differing_series_convention_has_its_own_identity() -> None:
    switched = replace(PROFILES, series_convention=SeriesConvention.REFERENCE_ODD_EVEN_ALTERNATION)
    with pytest.raises(ConventionMismatchError):
        runtime().accept(runtime(1, switched).outbound(config()), adapter().digest(config()))


def test_a_differing_profile_set_is_a_config_mismatch() -> None:
    switched = replace(PROFILES, key_id=KEY_ID)
    assert switched == PROFILES
    from mars777_police.app.interop_profiles import ToolNameProfile

    other = replace(PROFILES, tool_name_profile=ToolNameProfile.LECTURER_REFERENCE_ALIASES)
    with pytest.raises(ConfigMismatchError):
        runtime().accept(runtime(1, other).outbound(config()), adapter().digest(config()))


def test_an_unverifiable_proof_fails_closed_before_the_digest_is_compared() -> None:
    evidence = runtime().outbound(config())
    forged = ConfigLockEvidence(
        evidence.context, AuthProof(AuthProfile.HMAC_SHA256, KEY_ID, "0" * 64)
    )
    with pytest.raises(AuthFailureError):
        runtime().accept(forged, adapter().digest(config()))


def test_the_gate_permits_the_transition_only_when_every_condition_holds() -> None:
    evidence = runtime().outbound(config())
    digest = adapter().digest(config())
    gate = ConfigLockGate(True, digest, evidence, True)
    assert gate.may_lock
    machine = ProtocolMachine(ProtocolPhase.CONFIG_NEGOTIATION)
    assert gate.advance(machine).machine.phase is ProtocolPhase.CONFIG_LOCKED


@pytest.mark.parametrize("missing", ["converged", "digest", "evidence", "verified"])
def test_no_state_changes_when_any_single_gate_is_unmet(missing: str) -> None:
    evidence = runtime().outbound(config())
    digest = adapter().digest(config())
    gate = ConfigLockGate(
        missing != "converged",
        None if missing == "digest" else digest,
        None if missing == "evidence" else evidence,
        missing != "verified",
    )
    assert not gate.may_lock
    machine = ProtocolMachine(ProtocolPhase.CONFIG_NEGOTIATION)
    with pytest.raises(ConfigMismatchError):
        gate.advance(machine)
    assert machine.phase is ProtocolPhase.CONFIG_NEGOTIATION


def test_the_gate_delegates_legality_to_the_one_authoritative_graph() -> None:
    from mars777_police.app.state_machine import IllegalTransitionError

    gate = ConfigLockGate(True, Sha256Digest("0" * 64), runtime().outbound(config()), True)
    with pytest.raises(IllegalTransitionError):
        gate.advance(ProtocolMachine(ProtocolPhase.READY))
