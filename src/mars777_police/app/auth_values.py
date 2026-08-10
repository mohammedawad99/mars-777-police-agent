"""The authentication semantic values: profile, key label and proof.

**Representation only** (`SIGNATURE_AND_HASH_PROVENANCE.md` R12-FIX-A/B). Nothing
here computes or verifies an HMAC or an Ed25519 signature, and nothing reads key
material: this module imports no ``hmac``, ``hashlib``, ``cryptography`` or
``secrets``. A well-formed ``AuthProof`` is never a claim that it verifies.

The profile a verifier uses is **provisioned out of band before BOOT** and an
incoming ``auth_alg``/``key_id`` is *compared* against it, never used to select
the verifier - the algorithm-confusion defence frozen at Stage 4E-R12-FIX. That
comparison is a LIVE duty of the protocol layer, not of these values.
"""

from dataclasses import dataclass
from enum import StrEnum
from typing import Final

KEY_ID_MAX_LENGTH: Final[int] = 64
"""Parser bound on the non-secret key label."""

HMAC_SHA256_PROOF_LENGTH: Final[int] = 64
"""Characters in a 32-byte HMAC-SHA256 tag written in hexadecimal."""

ED25519_PROOF_LENGTH: Final[int] = 128
"""Characters in a 64-byte Ed25519 signature written in hexadecimal."""

_HEX_DIGITS: Final[frozenset[str]] = frozenset("0123456789abcdef")

_KEY_ID_CHARS: Final[frozenset[str]] = frozenset(
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789._-",
)
"""The exact frozen ASCII set ``[A-Za-z0-9._-]``.

ASCII is required so an identifier compared inside an authentication decision
never depends on Unicode normalisation.
"""


class InvalidKeyIdError(ValueError):
    """Raised when a string is not the locked key-label representation."""


class InvalidAuthProofError(ValueError):
    """Raised when an authentication proof is structurally malformed."""


class AuthProfile(StrEnum):
    """The closed set of keyed-authentication primitives.

    ``HMAC_SHA256`` is a **MAC**; ``ED25519`` is a **digital signature**. They are
    never interchangeable words. Plain unkeyed SHA-256 is deliberately absent: it
    authenticates nobody (`PRD06-FR-022`). The serialized value *is* the
    identifier - ``"HMAC-SHA256"``, ``"hmac_sha256"`` and ``"Ed25519"`` are not
    members and are refused, never folded.
    """

    HMAC_SHA256 = "HMAC_SHA256"
    ED25519 = "ED25519"


_PROOF_LENGTHS: Final[dict[AuthProfile, int]] = {
    AuthProfile.HMAC_SHA256: HMAC_SHA256_PROOF_LENGTH,
    AuthProfile.ED25519: ED25519_PROOF_LENGTH,
}


@dataclass(frozen=True, slots=True)
class KeyId:
    """A non-secret label naming the out-of-band provisioned key.

    It is a **label, never key material**: it must not be, contain or be derived
    from the key, which is why it may safely be serialized, logged and placed in
    error evidence. Compared exactly - never trimmed, never case-folded, never
    normalised, and an empty label never means "no key".
    """

    value: str

    def __post_init__(self) -> None:
        if type(self.value) is not str:
            raise InvalidKeyIdError(
                f"key_id must be a str, got {type(self.value).__name__}",
            )
        if not self.value:
            raise InvalidKeyIdError("key_id must be non-empty")
        if len(self.value) > KEY_ID_MAX_LENGTH:
            raise InvalidKeyIdError(
                f"key_id must be at most {KEY_ID_MAX_LENGTH} characters, got {len(self.value)}",
            )
        if not _KEY_ID_CHARS.issuperset(self.value):
            raise InvalidKeyIdError(
                "key_id must use only ASCII [A-Za-z0-9._-]; whitespace and"
                " non-ASCII are refused, never stripped or normalised",
            )


@dataclass(frozen=True, slots=True)
class AuthProof:
    """A profile-tagged authentication proof over some already-canonical core.

    Deliberately **not** a ``Sha256Digest``: that names the result of an unkeyed
    SHA-256, which neither a MAC nor a signature is, and the widths differ. The
    proof value is validated **against its own profile**, so a proof can never be
    read under a profile it did not declare.
    """

    profile: AuthProfile
    key_id: KeyId
    value: str

    def __post_init__(self) -> None:
        if type(self.profile) is not AuthProfile:
            raise InvalidAuthProofError(
                f"profile must be an AuthProfile, got {type(self.profile).__name__}",
            )
        if type(self.key_id) is not KeyId:
            raise InvalidAuthProofError(
                f"key_id must be a KeyId, got {type(self.key_id).__name__}",
            )
        if type(self.value) is not str:
            raise InvalidAuthProofError(
                f"proof must be a str, got {type(self.value).__name__}",
            )
        expected = _PROOF_LENGTHS[self.profile]
        if len(self.value) != expected:
            raise InvalidAuthProofError(
                f"{self.profile.value} proof must be exactly {expected} characters,"
                f" got {len(self.value)}",
            )
        if not _HEX_DIGITS.issuperset(self.value):
            raise InvalidAuthProofError(
                "proof must be lowercase hexadecimal; uppercase, whitespace,"
                " prefixes and base64 are refused, never normalised",
            )
