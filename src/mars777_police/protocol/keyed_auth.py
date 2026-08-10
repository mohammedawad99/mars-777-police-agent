"""Keyed authentication over `context ‖ canonical(core)` (JDEC-013, NDEC-005/007).

The **contract fixes the prefix, not a separator.** Every normative statement of
the construction - JDEC-013, NDEC-005, NDEC-007, `PRD06-FR-023`/`FR-043`,
INV-14/15, `FIELD_MATRIX` - writes it as `context ‖ canonical(core)` with the
two literal ASCII contexts `"step0"` and `"config"`, and no live document names
a separator byte, a length prefix or any other framing. This module therefore
implements exactly what is written: the context bytes followed by the canonical
bytes, and nothing invented in between. The result is unambiguous because
neither context is a prefix of the other and a canonical core always begins with
`{`, which is what the "fixed, unambiguous framing" clause requires of it.

**Non-self-reference:** the `{auth_alg, key_id, auth_tag}` envelope is never
inside the bytes it authenticates. **Domain separation:** a `"step0"` proof can
never verify as a `"config"` proof.

Key material is an injected runtime dependency and nothing else. It is never
loaded from a file or the environment here, never stored in a semantic value,
never serialized, never logged and never placed in an error message or a
`repr` - only the non-secret `key_id` ever appears.
"""

import hmac
from collections.abc import Mapping
from hashlib import sha256
from typing import Protocol

from ..app.auth_values import AuthProfile, AuthProof, KeyId
from ..app.protocol_errors import AuthFailureError
from .canonical import canonical_json_bytes

STEP0_CONTEXT = "step0"
CONFIG_CONTEXT = "config"
_CONTEXTS = (STEP0_CONTEXT, CONFIG_CONTEXT)


def auth_input(context: str, core: object) -> bytes:
    """Return the exact authenticated bytes for *context* over *core*."""
    if context not in _CONTEXTS:
        raise AuthFailureError(f"context must be one of {_CONTEXTS}, got {context!r}")
    return context.encode("utf-8") + canonical_json_bytes(core)


class AuthProvider(Protocol):
    """One keyed primitive, holding whatever key material it needs privately."""

    @property
    def profile(self) -> AuthProfile:
        """The single profile this provider implements."""
        ...

    def compute(self, key_id: KeyId, message: bytes) -> str:
        """Return the lowercase-hex proof value over *message*."""
        ...

    def verify(self, key_id: KeyId, message: bytes, value: str) -> bool:
        """Return whether *value* is a valid proof over *message*."""
        ...


class HmacSha256Provider:
    """The strict counted-match default: HMAC-SHA256 over the authenticated bytes.

    Keys arrive by dependency injection, keyed by the non-secret `key_id` text.
    Verification is `hmac.compare_digest`, so a wrong proof costs the same time
    as a right one.
    """

    def __init__(self, keys: Mapping[str, bytes]) -> None:
        self._keys = dict(keys)

    def __repr__(self) -> str:
        """Never render key material - not even its length."""
        return "HmacSha256Provider(keys=<withheld>)"

    @property
    def profile(self) -> AuthProfile:
        """This provider implements exactly `HMAC_SHA256`."""
        return AuthProfile.HMAC_SHA256

    def _key(self, key_id: KeyId) -> bytes:
        key = self._keys.get(key_id.value)
        if key is None:
            raise AuthFailureError(f"no key is provisioned for key_id {key_id.value!r}")
        return key

    def compute(self, key_id: KeyId, message: bytes) -> str:
        """Return the 64-character lowercase-hex HMAC-SHA256 tag."""
        return hmac.new(self._key(key_id), message, sha256).hexdigest()

    def verify(self, key_id: KeyId, message: bytes, value: str) -> bool:
        """Compare in constant time against the locally recomputed tag."""
        return hmac.compare_digest(self.compute(key_id, message), value)


class KeyedAuthenticator:
    """The `KeyedAuthPort` adapter: one provisioned profile, one provisioned key.

    The profile is fixed **before the first byte arrives**. An incoming
    `auth_alg`/`key_id` is *compared* against the provisioned expectation and
    never used to select the verifier, which is what makes an algorithm
    substitution ineffective rather than merely detectable. There is no
    fallback, no "try every profile" and no unkeyed path: a configured profile
    with no provider fails closed with `E-AUTH-FAILURE` before counted play.
    """

    def __init__(self, profile: AuthProfile, key_id: KeyId, provider: AuthProvider) -> None:
        if provider.profile is not profile:
            raise AuthFailureError(
                f"no provider is available for the provisioned profile {profile.value};"
                " a counted match refuses to play rather than fall back",
            )
        self._profile = profile
        self._key_id = key_id
        self._provider = provider

    def prove(self, context: str, core: object) -> AuthProof:
        """Return this peer's proof over *core* in *context*."""
        value = self._provider.compute(self._key_id, auth_input(context, core))
        return AuthProof(self._profile, self._key_id, value)

    def verify(self, context: str, core: object, proof: AuthProof) -> bool:
        """Return whether *proof* matches the provisioned expectation and verifies."""
        if proof.profile is not self._profile or proof.key_id != self._key_id:
            return False
        return self._provider.verify(self._key_id, auth_input(context, core), proof.value)
