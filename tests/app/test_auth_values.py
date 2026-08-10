"""Auth semantic values: closed profiles, exact key labels, profile-tagged proofs."""

import dataclasses

import pytest

from mars777_police.app.auth_values import (
    AuthProfile,
    AuthProof,
    InvalidAuthProofError,
    InvalidKeyIdError,
    KeyId,
)

HMAC_PROOF = "a" * 64
ED_PROOF = "b" * 128
KEY = KeyId("match-key_1.0")


def test_auth_profile_exact_members() -> None:
    assert [p.value for p in AuthProfile] == ["HMAC_SHA256", "ED25519"]


@pytest.mark.parametrize("alias", ["HMAC-SHA256", "hmac_sha256", "Ed25519", "SHA256"])
def test_auth_profile_rejects_aliases(alias: str) -> None:
    with pytest.raises(ValueError, match="is not a valid AuthProfile"):
        AuthProfile(alias)


def test_key_id_accepts_full_frozen_charset() -> None:
    charset = "ABCabc019._-"
    assert KeyId(charset).value == charset
    assert KeyId("k" * 64).value == "k" * 64


def test_key_id_preserves_case_and_is_immutable() -> None:
    assert KeyId("AbC") != KeyId("abc")
    with pytest.raises(dataclasses.FrozenInstanceError):
        KeyId("a").value = "b"  # type: ignore[misc]


@pytest.mark.parametrize("bad", [None, 1, b"k", True])
def test_key_id_rejects_non_str(bad: object) -> None:
    with pytest.raises(InvalidKeyIdError, match="must be a str"):
        KeyId(bad)  # type: ignore[arg-type]


def test_key_id_rejects_empty() -> None:
    with pytest.raises(InvalidKeyIdError, match="non-empty"):
        KeyId("")


def test_key_id_rejects_over_max_length() -> None:
    with pytest.raises(InvalidKeyIdError, match="at most 64"):
        KeyId("k" * 65)


@pytest.mark.parametrize("bad", ["a b", " a", "a ", "a\tb", "kéy", "k/y", "k+y", "k:y"])
def test_key_id_rejects_charset_violations(bad: str) -> None:
    with pytest.raises(InvalidKeyIdError, match=r"ASCII \[A-Za-z0-9\._-\]"):
        KeyId(bad)


def test_hmac_proof_valid() -> None:
    proof = AuthProof(AuthProfile.HMAC_SHA256, KEY, HMAC_PROOF)
    assert proof.value == HMAC_PROOF
    assert proof == AuthProof(AuthProfile.HMAC_SHA256, KEY, HMAC_PROOF)


def test_ed25519_proof_valid() -> None:
    assert AuthProof(AuthProfile.ED25519, KEY, ED_PROOF).value == ED_PROOF


def test_proof_is_immutable() -> None:
    with pytest.raises(dataclasses.FrozenInstanceError):
        AuthProof(AuthProfile.HMAC_SHA256, KEY, HMAC_PROOF).value = HMAC_PROOF  # type: ignore[misc]


@pytest.mark.parametrize("bad", ["HMAC_SHA256", None, 1])
def test_proof_rejects_non_profile(bad: object) -> None:
    with pytest.raises(InvalidAuthProofError, match="must be an AuthProfile"):
        AuthProof(bad, KEY, HMAC_PROOF)  # type: ignore[arg-type]


@pytest.mark.parametrize("bad", ["match-key", None])
def test_proof_rejects_raw_key_id(bad: object) -> None:
    with pytest.raises(InvalidAuthProofError, match="must be a KeyId"):
        AuthProof(AuthProfile.HMAC_SHA256, bad, HMAC_PROOF)  # type: ignore[arg-type]


@pytest.mark.parametrize("bad", [None, 1, b"a" * 64])
def test_proof_rejects_non_str_value(bad: object) -> None:
    with pytest.raises(InvalidAuthProofError, match="proof must be a str"):
        AuthProof(AuthProfile.HMAC_SHA256, KEY, bad)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("profile", "value", "expected"),
    [
        (AuthProfile.HMAC_SHA256, "a" * 63, "exactly 64"),
        (AuthProfile.HMAC_SHA256, "a" * 65, "exactly 64"),
        (AuthProfile.HMAC_SHA256, ED_PROOF, "exactly 64"),
        (AuthProfile.ED25519, "b" * 127, "exactly 128"),
        (AuthProfile.ED25519, "b" * 129, "exactly 128"),
        (AuthProfile.ED25519, HMAC_PROOF, "exactly 128"),
    ],
)
def test_proof_widths_are_profile_exact(profile: AuthProfile, value: str, expected: str) -> None:
    with pytest.raises(InvalidAuthProofError, match=expected):
        AuthProof(profile, KEY, value)


@pytest.mark.parametrize("bad", ["A" * 64, "g" * 64, "0x" + "a" * 62, " " + "a" * 63])
def test_proof_rejects_non_lower_hex(bad: str) -> None:
    with pytest.raises(InvalidAuthProofError, match="lowercase hexadecimal"):
        AuthProof(AuthProfile.HMAC_SHA256, KEY, bad)
