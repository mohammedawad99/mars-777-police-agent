"""The commitment nonce as a protocol semantic value.

The source requires a *fresh cryptographic* nonce, secret until the final
reveal, with every nonce eventually revealed (Ch 5 p.50-51, §5.4 p.55). It fixes
no encoding: `secrets.token_hex(16)` is REFERENCE-EXAMPLE. Stage 4E-R6-FIX2
froze the current-v1 counted-match profile as exactly `[0-9a-f]{32}` - a
**PROJECT-CONTRACT**, kept for strict parsing and NFC stability, *not* because
recomputation needs it: a receiver rebuilds the record from the exact revealed
string.

The split that matters here: this value validates **representation** only.
Freshness, entropy and CSPRNG provenance are producer duties a constructor
handed a *received* string can never verify, so `"0" * 32` is deliberately
valid. Secrecy until final reveal is a protocol invariant, not a field.
"""

import dataclasses

import pytest

from mars777_police.app.protocol_values import (
    InvalidDigestError,
    InvalidNonceError,
    NonceValue,
    Sha256Digest,
)

VALID = "0123456789abcdef0123456789abcdef"


def test_the_nonce_carries_exactly_its_representation() -> None:
    assert tuple(f.name for f in dataclasses.fields(NonceValue)) == ("value",)


@pytest.mark.parametrize("text", ["0" * 32, "f" * 32, VALID, "a1b2c3d4e5f60718293a4b5c6d7e8f90"])
def test_every_well_formed_nonce_is_accepted_verbatim(text: str) -> None:
    """Stored exactly as given - there is no normalization step to disagree with."""
    assert NonceValue(text).value == text


def test_a_low_entropy_nonce_is_still_structurally_valid() -> None:
    """Entropy is the producer's CSPRNG duty; a received string cannot prove it."""
    assert NonceValue("0" * 32).value == "0" * 32


@pytest.mark.parametrize(
    "value",
    [None, True, False, 0, 1, b"0" * 32, ["0" * 32], ("0" * 32,), {"value": "0" * 32}, object()],
)
def test_a_nonce_of_the_wrong_type_is_refused_never_coerced(value: object) -> None:
    with pytest.raises(InvalidNonceError):
        NonceValue(value)  # type: ignore[arg-type]


def test_a_str_subclass_is_refused() -> None:
    class LoudNonce(str):
        pass

    with pytest.raises(InvalidNonceError):
        NonceValue(LoudNonce(VALID))


@pytest.mark.parametrize("text", ["", "0", "0" * 31, "0" * 33, "0" * 64])
def test_a_nonce_of_the_wrong_length_is_refused(text: str) -> None:
    with pytest.raises(InvalidNonceError):
        NonceValue(text)


@pytest.mark.parametrize(
    "text",
    [
        "0123456789ABCDEF0123456789abcdef",
        VALID.upper(),
        "0123456789AbCdEf0123456789abcdef",
        " " + VALID[1:],
        VALID[:-1] + " ",
        VALID[:16] + " " + VALID[17:],
        "0x" + VALID[2:],
        VALID[:8] + "-" + VALID[9:],
        VALID[:8] + ":" + VALID[9:],
        VALID[:8] + "_" + VALID[9:],
        VALID[:-1] + "\n",
        VALID[:-1] + "\t",
        VALID[:-1] + "g",
        "\u0660" * 32,  # ARABIC-INDIC ZERO: a lookalike, not a hex digit
        "0123456789abcdef0123456789abcde\uff46",  # FULLWIDTH f
    ],
)
def test_a_nonce_outside_the_locked_profile_is_refused_never_normalised(text: str) -> None:
    """Uppercase, whitespace, prefixes and separators raise - they are never fixed up."""
    with pytest.raises(InvalidNonceError):
        NonceValue(text)


def test_the_nonce_is_frozen_slotted_and_value_equal() -> None:
    nonce = NonceValue(VALID)
    with pytest.raises(dataclasses.FrozenInstanceError):
        nonce.value = "f" * 32  # type: ignore[misc]
    assert not hasattr(nonce, "__dict__")
    assert NonceValue.__slots__ == ("value",)
    assert nonce == NonceValue(VALID)
    assert nonce != NonceValue("f" * 32)


def test_a_nonce_is_not_a_digest_even_though_both_are_hex() -> None:
    """Different values with different lengths; neither is interchangeable."""
    assert NonceValue is not Sha256Digest
    assert not issubclass(NonceValue, Sha256Digest)
    with pytest.raises(InvalidDigestError):
        Sha256Digest(VALID)
    with pytest.raises(InvalidNonceError):
        NonceValue("0" * 64)


def test_malformed_construction_is_a_value_error_of_its_own_narrow_type() -> None:
    assert issubclass(InvalidNonceError, ValueError)
    assert not issubclass(InvalidNonceError, InvalidDigestError)
    with pytest.raises(ValueError):
        NonceValue("nope")


def test_the_value_neither_generates_randomness_nor_verifies_anything() -> None:
    """R8 is representation only: generation and verification are later slices."""
    from mars777_police.app import protocol_values

    for forbidden in ("secrets", "random", "os", "uuid", "hashlib", "time", "json"):
        assert not hasattr(protocol_values, forbidden)
    for method in ("generate", "random", "fresh", "verify", "matches", "is_fresh"):
        assert not hasattr(NonceValue, method)


def test_the_nonce_is_on_the_exhaustive_app_surface() -> None:
    from mars777_police import app

    assert app.NonceValue is NonceValue
    assert app.InvalidNonceError is InvalidNonceError
    assert {"NonceValue", "InvalidNonceError"} <= set(app.__all__)
