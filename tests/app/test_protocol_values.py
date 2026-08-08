"""Shared protocol value representations: digest text and the audit verdict.

`Sha256Digest` validates a **representation**, never a computation: SHA-256 is
source-explicit (App E #17), hex is project-locked, 64 chars follow from SHA-256
in hex, and **lowercase is a PROJECT-CONTRACT** - the one repository
`.hexdigest()` sits in a block labelled "the reference", so uppercase is
*rejected*, never rewritten (D23/D24). Its error is a `ValueError`, matching
`FinalAuditVerdict("OK")`. That verdict is the closed pair `LOG_CONTRACT.md`
freezes for `audit.result` (Ch 7 p.72-74) - not the Event-8 move verdict, the
Event-9 `verified` record, intent classification, or a technical loss.
"""

import dataclasses

import pytest

from mars777_police.app.protocol_values import (
    FinalAuditVerdict,
    InvalidDigestError,
    Sha256Digest,
)

ZEROES = "0" * 64
EFFS = "f" * 64
MIXED = "0123456789abcdef" * 4


def test_the_digest_carries_exactly_one_representation_field() -> None:
    assert tuple(f.name for f in dataclasses.fields(Sha256Digest)) == ("value",)


def test_the_digest_is_frozen_slotted_and_value_equal() -> None:
    digest = Sha256Digest(ZEROES)
    with pytest.raises(dataclasses.FrozenInstanceError):
        digest.value = EFFS  # type: ignore[misc]
    assert not hasattr(digest, "__dict__")
    assert Sha256Digest.__slots__ == ("value",)
    assert digest == Sha256Digest(ZEROES)
    assert digest != Sha256Digest(EFFS)


@pytest.mark.parametrize("text", [ZEROES, EFFS, MIXED])
def test_valid_lowercase_64_hex_is_accepted(text: str) -> None:
    assert Sha256Digest(text).value == text


@pytest.mark.parametrize("length", [0, 1, 63, 65, 128])
def test_any_length_other_than_64_is_refused(length: int) -> None:
    with pytest.raises(InvalidDigestError):
        Sha256Digest("a" * length)


UPPER = ["A" * 64, "F" * 64, MIXED.upper(), MIXED[:48] + MIXED[48:].upper(), ZEROES[:-1] + "A"]
NON_HEX = ["g" * 64, "z" * 64, ZEROES[:-1] + "g", ZEROES[:-1] + "-", "0x" + "0" * 62]


@pytest.mark.parametrize("text", UPPER)
def test_uppercase_hex_is_refused_and_never_normalised(text: str) -> None:
    """Lowercase is a PROJECT-CONTRACT; a wrong spelling stays wrong."""
    with pytest.raises(InvalidDigestError):
        Sha256Digest(text)


@pytest.mark.parametrize("text", NON_HEX)
def test_non_hexadecimal_characters_are_refused(text: str) -> None:
    with pytest.raises(InvalidDigestError):
        Sha256Digest(text)


WHITESPACE = [" " + ZEROES[1:], ZEROES[:-1] + " ", ZEROES[:-1] + "\n", " " + ZEROES]


@pytest.mark.parametrize("text", WHITESPACE)
def test_whitespace_is_refused_and_never_stripped(text: str) -> None:
    with pytest.raises(InvalidDigestError):
        Sha256Digest(text)


NON_STR = [None, 0, 1, True, False, 1.0, b"0" * 64, bytearray(b"0" * 64), object(), []]


@pytest.mark.parametrize("value", NON_STR)
def test_non_string_input_is_refused(value: object) -> None:
    with pytest.raises(InvalidDigestError):
        Sha256Digest(value)  # type: ignore[arg-type]


def test_the_digest_neither_orders_computes_nor_names_a_hash() -> None:
    """Representation only: no ordering, no hashing, no notion of purpose."""
    with pytest.raises(TypeError):
        _ = Sha256Digest(ZEROES) < Sha256Digest(EFFS)  # type: ignore[operator]
    for name in ("compute", "of_bytes", "digest", "hexdigest", "verify", "matches", "purpose"):
        assert not hasattr(Sha256Digest, name)


def test_the_audit_verdict_is_exactly_two_members() -> None:
    assert len(FinalAuditVerdict) == 2
    assert {member.value for member in FinalAuditVerdict} == {"Verified OK", "TAMPERED"}


def test_the_audit_verdict_values_are_the_frozen_literals() -> None:
    assert FinalAuditVerdict("Verified OK") is FinalAuditVerdict.VERIFIED_OK
    assert FinalAuditVerdict("TAMPERED") is FinalAuditVerdict.TAMPERED


@pytest.mark.parametrize(
    "text",
    ["OK", "Verified", "verified ok", "VERIFIED OK", "tampered", "TAMPERED ", "PASS", "FAIL"],
)
def test_wrong_spellings_are_refused_and_never_normalised(text: str) -> None:
    with pytest.raises(ValueError, match="is not a valid"):
        FinalAuditVerdict(text)


@pytest.mark.parametrize("value", [True, False, 0, 1, None])
def test_booleans_and_integers_are_not_verdicts(value: object) -> None:
    with pytest.raises(ValueError, match="is not a valid"):
        FinalAuditVerdict(value)


def test_the_audit_verdict_excludes_every_neighbouring_concept() -> None:
    names = {member.name for member in FinalAuditVerdict}
    for absent in ("PASS", "FAIL", "VALID", "INVALID", "OK", "TECHNICAL_LOSS", "ACCEPT", "REJECT"):
        assert absent not in names


def test_the_digest_error_is_a_value_construction_error() -> None:
    """Malformed representation is a ValueError, like `FinalAuditVerdict("OK")`."""
    assert issubclass(InvalidDigestError, ValueError)


def test_the_digest_error_is_on_the_public_app_surface() -> None:
    from mars777_police import app

    assert app.InvalidDigestError is InvalidDigestError
    assert "InvalidDigestError" in app.__all__


@pytest.mark.parametrize("text", [UPPER[0], NON_HEX[0], ZEROES[:-1] + " ", "a" * 63])
def test_a_malformed_digest_is_catchable_narrowly_and_generically(text: str) -> None:
    with pytest.raises(InvalidDigestError):
        Sha256Digest(text)
    with pytest.raises(ValueError):
        Sha256Digest(text)


def test_the_verdict_keeps_native_value_error_semantics() -> None:
    with pytest.raises(ValueError):
        FinalAuditVerdict("OK")
