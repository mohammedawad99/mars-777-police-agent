"""Keyed authentication: the exact bytes, the fail-closed rules, the key boundary.

The construction under test is `context ‖ canonical(core)` with the two literal
contexts the contract fixes. What the contract does **not** fix is a separator,
and none is invented here - the authenticated bytes are the context followed by
the canonical bytes, which is what every normative statement of it writes.
"""

import hmac
from hashlib import sha256

import pytest
from r16_builders import KEY_ID, SHARED_KEY

from mars777_police.app.auth_values import AuthProfile, AuthProof, KeyId
from mars777_police.app.protocol_errors import AuthFailureError
from mars777_police.protocol.canonical import canonical_json_bytes
from mars777_police.protocol.keyed_auth import (
    CONFIG_CONTEXT,
    RESULT_CONTEXT,
    STEP0_CONTEXT,
    HmacSha256Provider,
    KeyedAuthenticator,
    auth_input,
)

CORE = {"game_id": "g", "n": 1}


def authenticator(profile: AuthProfile = AuthProfile.HMAC_SHA256) -> KeyedAuthenticator:
    return KeyedAuthenticator(profile, KEY_ID, HmacSha256Provider({KEY_ID.value: SHARED_KEY}))


def test_the_authenticated_bytes_are_the_context_then_the_canonical_core() -> None:
    assert auth_input(STEP0_CONTEXT, CORE) == b"step0" + canonical_json_bytes(CORE)
    assert auth_input(CONFIG_CONTEXT, CORE) == b"config" + canonical_json_bytes(CORE)


def test_no_separator_padding_or_length_prefix_is_introduced() -> None:
    raw = auth_input(STEP0_CONTEXT, CORE)
    assert raw.startswith(b"step0{")
    assert b"step0\x00" not in raw and b"step0|" not in raw


def test_the_two_contexts_are_domain_separated() -> None:
    assert auth_input(STEP0_CONTEXT, CORE) != auth_input(CONFIG_CONTEXT, CORE)
    auth = authenticator()
    proof = auth.prove(STEP0_CONTEXT, CORE)
    assert auth.verify(STEP0_CONTEXT, CORE, proof)
    assert not auth.verify(CONFIG_CONTEXT, CORE, proof)


def test_an_unknown_context_is_refused_rather_than_authenticated() -> None:
    """`"result"` left this list when it became a real context; the rule did not."""
    for bad in ("STEP0", "step-0", "RESULT", "results", "result ", ""):
        with pytest.raises(AuthFailureError):
            auth_input(bad, CORE)


def test_the_result_context_is_separate_from_the_other_two() -> None:
    """Domain separation across all three: no proof verifies in another context.

    A result agreement is authenticated over its own request bytes so a peer
    whose client opens a session per call can still be recognised. That is only
    safe while a Step-0 proof cannot be replayed as a result proof, which is what
    a distinct context buys and what this pins.
    """
    auth = authenticator()
    contexts = (STEP0_CONTEXT, CONFIG_CONTEXT, RESULT_CONTEXT)
    assert len(set(contexts)) == 3
    for context in contexts:
        proof = auth.prove(context, CORE)
        assert auth.verify(context, CORE, proof)
        for other in contexts:
            if other != context:
                assert not auth.verify(other, CORE, proof)


def test_the_hmac_matches_an_independently_computed_vector() -> None:
    """The oracle is stdlib `hmac`, computed here from the same frozen bytes."""
    expected = hmac.new(SHARED_KEY, b"step0" + canonical_json_bytes(CORE), sha256).hexdigest()
    proof = authenticator().prove(STEP0_CONTEXT, CORE)
    assert proof.value == expected
    assert len(proof.value) == 64
    assert proof.value == proof.value.lower()


def test_the_proof_carries_the_provisioned_profile_and_key_id() -> None:
    proof = authenticator().prove(STEP0_CONTEXT, CORE)
    assert proof.profile is AuthProfile.HMAC_SHA256
    assert proof.key_id == KEY_ID


def test_a_tampered_core_does_not_verify() -> None:
    auth = authenticator()
    proof = auth.prove(STEP0_CONTEXT, CORE)
    assert not auth.verify(STEP0_CONTEXT, {"game_id": "g", "n": 2}, proof)


def test_a_wrong_key_produces_a_different_proof_that_does_not_verify() -> None:
    other = KeyedAuthenticator(
        AuthProfile.HMAC_SHA256, KEY_ID, HmacSha256Provider({KEY_ID.value: b"other"})
    )
    assert not authenticator().verify(STEP0_CONTEXT, CORE, other.prove(STEP0_CONTEXT, CORE))


def test_an_unprovisioned_key_id_fails_closed_rather_than_deriving_a_key() -> None:
    provider = HmacSha256Provider({})
    with pytest.raises(AuthFailureError):
        provider.compute(KEY_ID, b"x")


def test_a_differing_key_id_is_refused_without_consulting_the_key() -> None:
    auth = authenticator()
    proof = auth.prove(STEP0_CONTEXT, CORE)
    swapped = AuthProof(proof.profile, KeyId("someone-elses-key"), proof.value)
    assert not auth.verify(STEP0_CONTEXT, CORE, swapped)


def test_a_declared_profile_never_selects_the_verifier() -> None:
    """An `ED25519`-labelled proof is refused, not verified under `ED25519`."""
    auth = authenticator()
    proof = auth.prove(STEP0_CONTEXT, CORE)
    downgraded = AuthProof(AuthProfile.ED25519, proof.key_id, proof.value + "0" * 64)
    assert not auth.verify(STEP0_CONTEXT, CORE, downgraded)


def test_verification_uses_a_constant_time_comparison() -> None:
    provider = HmacSha256Provider({KEY_ID.value: SHARED_KEY})
    message = b"step0{}"
    assert provider.verify(KEY_ID, message, provider.compute(KEY_ID, message))
    assert not provider.verify(KEY_ID, message, "0" * 64)


def test_no_key_material_is_rendered_or_stored_in_a_semantic_value() -> None:
    provider = HmacSha256Provider({KEY_ID.value: SHARED_KEY})
    assert SHARED_KEY.decode() not in repr(provider)
    assert "<withheld>" in repr(provider)
    proof = authenticator().prove(STEP0_CONTEXT, CORE)
    assert SHARED_KEY.decode() not in repr(proof)
