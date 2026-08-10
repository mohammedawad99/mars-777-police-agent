"""Profile dispatch: `ED25519` is supported, faked and fallen back to never.

`ED25519` is a **pre-agreed compatibility** profile, and no dependency was added
to satisfy it. The runtime dispatches to a caller-supplied provider through the
frozen port boundary; a match configured for it with no provider available
**fails closed** before play, with an existing error identity.
"""

import pytest
from r16_builders import KEY_ID, SHARED_KEY

from mars777_police.app.auth_values import AuthProfile
from mars777_police.app.protocol_errors import AuthFailureError
from mars777_police.protocol.keyed_auth import (
    STEP0_CONTEXT,
    HmacSha256Provider,
    KeyedAuthenticator,
    auth_input,
)

CORE = {"game_id": "g"}


class StubEd25519Provider:
    """A conforming `ED25519` provider; the signature scheme itself is the caller's."""

    def __init__(self, signature: str = "e" * 128) -> None:
        self.signature = signature
        self.messages: list[bytes] = []

    @property
    def profile(self) -> AuthProfile:
        return AuthProfile.ED25519

    def compute(self, key_id: object, message: bytes) -> str:
        self.messages.append(message)
        return self.signature

    def verify(self, key_id: object, message: bytes, value: str) -> bool:
        return value == self.signature and message in self.messages


def test_ed25519_dispatches_to_the_supplied_provider_over_the_same_bytes() -> None:
    provider = StubEd25519Provider()
    auth = KeyedAuthenticator(AuthProfile.ED25519, KEY_ID, provider)
    proof = auth.prove(STEP0_CONTEXT, CORE)
    assert proof.profile is AuthProfile.ED25519
    assert len(proof.value) == 128
    assert provider.messages == [auth_input(STEP0_CONTEXT, CORE)]
    assert auth.verify(STEP0_CONTEXT, CORE, proof)


def test_a_configured_profile_with_no_matching_provider_fails_closed() -> None:
    with pytest.raises(AuthFailureError):
        KeyedAuthenticator(
            AuthProfile.ED25519, KEY_ID, HmacSha256Provider({KEY_ID.value: SHARED_KEY})
        )


def test_there_is_no_fallback_from_ed25519_to_hmac() -> None:
    """A missing provider refuses the match; it never quietly becomes a MAC."""
    with pytest.raises(AuthFailureError) as failure:
        KeyedAuthenticator(
            AuthProfile.ED25519, KEY_ID, HmacSha256Provider({KEY_ID.value: SHARED_KEY})
        )
    assert "fall back" in str(failure.value)
    assert failure.value.error_id == "E-AUTH-FAILURE"


def test_an_hmac_proof_never_verifies_under_an_ed25519_authenticator() -> None:
    hmac_auth = KeyedAuthenticator(
        AuthProfile.HMAC_SHA256, KEY_ID, HmacSha256Provider({KEY_ID.value: SHARED_KEY})
    )
    ed_auth = KeyedAuthenticator(AuthProfile.ED25519, KEY_ID, StubEd25519Provider())
    assert not ed_auth.verify(STEP0_CONTEXT, CORE, hmac_auth.prove(STEP0_CONTEXT, CORE))


def test_no_signature_library_was_introduced_by_this_module() -> None:
    from mars777_police.protocol import keyed_auth

    for forbidden in ("cryptography", "nacl", "ed25519", "Ed25519PrivateKey"):
        assert not hasattr(keyed_auth, forbidden)
