"""Immutable shared protocol semantic value representations.

The primitives peer-message contracts and the outer protocol implementations
must agree on. **Representation only**: nothing here computes a hash, produces
canonical bytes, serializes, or knows which core a digest was taken over -
`protocol.canonical` and `protocol.commitment` own that, and they consume these
values at runtime (`MODULE_BOUNDARIES.md`, Stage 4F-R1/FIX1). No state is owned.

Provenance of the digest contract, kept deliberately separate:

* **SHA-256** is the algorithm - SOURCE-EXPLICIT (App E #17).
* **Hexadecimal** text is PROJECT-LOCKED (`FIELD_MATRIX.md` types the Step-0 and
  config auth tags and the result approval hash ``string(hex)``).
* **64 characters** is *entailed* by a SHA-256 digest written in hex.
* **Lowercase** is a **PROJECT-CONTRACT** and nothing more. No source or locked
  contract fixes the case; the only ``.hexdigest()`` in the repository sits in a
  block `CANONICALIZATION_CONTRACT.md` itself labels "the reference". Lowercase
  is chosen so one digest never has two spellings - `config_sha256` equality is
  a protocol decision point - and an uppercase spelling is therefore **rejected,
  never rewritten**. Should a peer ever send another spelling, normalizing it is
  a `protocol.messages` wire-mapping concern, not this value's.
"""

from dataclasses import dataclass
from enum import StrEnum
from typing import Final

SHA256_HEX_LENGTH: Final[int] = 64
"""Characters in a SHA-256 digest written in hexadecimal."""

NONCE_HEX_LENGTH: Final[int] = 32
"""Characters in the current-v1 commitment nonce - 16 bytes written in hex.

**PROJECT-CONTRACT**, not source law (Stage 4E-R6-FIX2). The book requires a
*fresh cryptographic* nonce and fixes no encoding; ``secrets.token_hex(16)`` is
REFERENCE-EXAMPLE. The profile is fixed for strict parsing and stability under
the canonicalization NFC step - **not** because recomputation needs it, since a
receiver rebuilds the sealed record from the exact string the sender revealed.
Current v1 supports this one representation; both peers echo it before
``CONFIG_LOCKED`` and a mismatch refuses counted play there (NDEC-001).
"""

_HEX_DIGITS: Final[frozenset[str]] = frozenset("0123456789abcdef")
"""The lowercase hexadecimal alphabet; uppercase is deliberately absent."""


class InvalidDigestError(ValueError):
    """Raised when a string is not the locked digest representation.

    A ``ValueError``: this is malformed value construction, never stale input,
    a hash mismatch, a replay mismatch or a tampering verdict. Subclassing it
    keeps the module coherent with ``FinalAuditVerdict("OK")``, which raises
    ``ValueError`` natively, so a caller may catch either the narrow type or
    the built-in category.
    """


class InvalidNonceError(ValueError):
    """Raised when a string is not the locked nonce representation.

    Malformed value construction only. **Not** a profile mismatch (a live
    pre-match negotiation refusal), not failed freshness or entropy (producer
    duties), not a broken secrecy invariant, not a duplicate or stale nonce and
    not a commitment mismatch - each of those is owned elsewhere entirely.
    """


@dataclass(frozen=True, slots=True)
class Sha256Digest:
    """A validated textual SHA-256 digest.

    It carries no notion of *which* digest it is: the same representation backs
    ``H_commit``, ``config_sha256`` and ``result_sha256``, and the field that
    holds the value supplies that meaning. Structural validation only - a
    well-formed value is never a claim that it is the digest of anything.
    """

    value: str

    def __post_init__(self) -> None:
        if type(self.value) is not str:
            raise InvalidDigestError(
                f"digest must be a str, got {type(self.value).__name__}",
            )
        if len(self.value) != SHA256_HEX_LENGTH:
            raise InvalidDigestError(
                f"digest must be exactly {SHA256_HEX_LENGTH} characters, got {len(self.value)}",
            )
        if not _HEX_DIGITS.issuperset(self.value):
            raise InvalidDigestError(
                "digest must be lowercase hexadecimal; uppercase, whitespace,"
                " prefixes and separators are refused, never normalised",
            )


class FinalAuditVerdict(StrEnum):
    """The closed final-audit vocabulary of `LOG_CONTRACT.md` ``audit.result``.

    Exactly the two states Ch 7 p.72-74 freezes. This is the **final**
    cryptographic/replay outcome - not the Event-8 move-validation response, not
    the Event-9 per-step ``verified`` record, not ``intent`` classification and
    not a technical loss, all of which are separate concepts with their own
    (still unfrozen) representations.
    """

    VERIFIED_OK = "Verified OK"
    TAMPERED = "TAMPERED"


@dataclass(frozen=True, slots=True)
class NonceValue:
    """A validated commitment nonce in the current-v1 representation.

    Structural validation **only**: the value proves how a string is written,
    never how it was produced. A constructor handed a *received* string cannot
    show it came from a CSPRNG, so freshness, entropy and provenance stay
    producer duties (CRYPTO-010) and secrecy-until-final-reveal stays a protocol
    invariant. ``"0" * 32`` is therefore deliberately valid here and would be a
    generator defect, caught somewhere else entirely.
    """

    value: str

    def __post_init__(self) -> None:
        if type(self.value) is not str:
            raise InvalidNonceError(
                f"nonce must be a str, got {type(self.value).__name__}",
            )
        if len(self.value) != NONCE_HEX_LENGTH:
            raise InvalidNonceError(
                f"nonce must be exactly {NONCE_HEX_LENGTH} characters, got {len(self.value)}",
            )
        if not _HEX_DIGITS.issuperset(self.value):
            raise InvalidNonceError(
                "nonce must be lowercase hexadecimal; uppercase, whitespace,"
                " prefixes and separators are refused, never normalised",
            )
