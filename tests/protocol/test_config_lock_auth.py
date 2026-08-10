"""The lock context: what it binds, and what it refuses to bind.

A proof over the App-B core alone would be valid for every sub-game of the
series. The lock context is what makes a proof mean *this* game, *this*
sub-game, *this* digest and *these* profiles - and the App-B core enters it only
through the digest, so the physics contract is never polluted with protocol
metadata.
"""

from dataclasses import replace

from r16_builders import GAME_ID, GAME_UID, KEY_ID, PROFILES, SHARED_KEY, config

from mars777_police.app.auth_values import AuthProfile
from mars777_police.app.interop_profiles import SeriesConvention
from mars777_police.app.peer_pregame_messages import ConfigLockContext
from mars777_police.domain.config_sections import WorldTerms
from mars777_police.protocol.canonical import canonical_json_bytes
from mars777_police.protocol.config_lock import (
    ConfigLockAuthenticator,
    config_sha256,
    lock_context_core,
)
from mars777_police.protocol.keyed_auth import HmacSha256Provider, KeyedAuthenticator


def authenticator() -> ConfigLockAuthenticator:
    return ConfigLockAuthenticator(
        KeyedAuthenticator(
            AuthProfile.HMAC_SHA256, KEY_ID, HmacSha256Provider({KEY_ID.value: SHARED_KEY})
        )
    )


def context(sub_game: int = 1) -> ConfigLockContext:
    return ConfigLockContext(GAME_ID, GAME_UID, sub_game, config_sha256(config()), PROFILES)


def test_the_context_binds_identity_sub_game_digest_and_profiles() -> None:
    core = lock_context_core(context())
    assert set(core) == {"game_id", "game_uid", "sub_game", "config_sha256", "profiles"}
    assert core["config_sha256"] == config_sha256(config()).value
    assert isinstance(core["profiles"], dict)
    assert len(core["profiles"]) == 11


def test_no_app_b_core_member_appears_individually_in_the_context() -> None:
    raw = canonical_json_bytes(lock_context_core(context()))
    for forbidden in (b"grid_size", b"move_set", b"pheromone_decay", b"scoring"):
        assert forbidden not in raw


def test_the_envelope_is_never_inside_the_bytes_it_authenticates() -> None:
    raw = canonical_json_bytes(lock_context_core(context()))
    assert b"auth_tag" not in raw and b"auth_alg" not in raw
    assert b"HMAC_SHA256" in raw  # the profile, bound as data, not as an envelope


def test_a_proof_verifies_over_its_own_context() -> None:
    auth = authenticator()
    assert auth.verify(context(), auth.prove(context()))


def test_a_proof_does_not_carry_across_sub_games() -> None:
    auth = authenticator()
    assert not auth.verify(context(2), auth.prove(context(1)))


def test_a_proof_does_not_carry_across_a_changed_config() -> None:
    auth = authenticator()
    proof = auth.prove(context())
    other = replace(config(), world=WorldTerms("New York", 16))
    moved = ConfigLockContext(GAME_ID, GAME_UID, 1, config_sha256(other), PROFILES)
    assert not auth.verify(moved, proof)


def test_a_proof_does_not_carry_across_a_changed_profile_set() -> None:
    auth = authenticator()
    proof = auth.prove(context())
    switched = replace(PROFILES, series_convention=SeriesConvention.REFERENCE_ODD_EVEN_ALTERNATION)
    moved = ConfigLockContext(GAME_ID, GAME_UID, 1, config_sha256(config()), switched)
    assert not auth.verify(moved, proof)


def test_the_adapter_recomputes_the_digest_locally() -> None:
    assert authenticator().digest(config()) == config_sha256(config())


def test_the_config_and_step0_contexts_produce_different_proofs() -> None:
    from mars777_police.protocol.keyed_auth import CONFIG_CONTEXT, STEP0_CONTEXT, auth_input

    core = lock_context_core(context())
    assert auth_input(CONFIG_CONTEXT, core) != auth_input(STEP0_CONTEXT, core)
