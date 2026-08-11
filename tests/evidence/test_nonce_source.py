"""The one place the system decides what a fresh nonce is.

`NonceValue` says outright that it proves how a string is written, never how it
was produced. These tests cover the half the type deliberately cannot.
"""

import pytest
from evidence_builders import ScriptedNonces

from mars777_police.app.protocol_values import NONCE_HEX_LENGTH, InvalidNonceError, NonceValue
from mars777_police.protocol.secure_nonce import NONCE_BYTES, SecretsNonceSource


def test_a_fresh_nonce_is_the_frozen_semantic_value() -> None:
    nonce = SecretsNonceSource().fresh()
    assert type(nonce) is NonceValue
    assert len(nonce.value) == NONCE_HEX_LENGTH


def test_the_byte_width_is_derived_from_the_frozen_hex_length() -> None:
    """16 bytes, and it can never drift from the profile it renders into."""
    assert NONCE_BYTES == NONCE_HEX_LENGTH // 2 == 16


def test_the_provider_uses_the_cryptographic_source(monkeypatch: pytest.MonkeyPatch) -> None:
    """Not `random`, not a counter, not a clock: `secrets.token_hex`."""
    calls: list[int] = []

    def spy(size: int) -> str:
        calls.append(size)
        return "a" * NONCE_HEX_LENGTH

    monkeypatch.setattr("mars777_police.protocol.secure_nonce.secrets.token_hex", spy)
    assert SecretsNonceSource().fresh().value == "a" * NONCE_HEX_LENGTH
    assert calls == [NONCE_BYTES]


def test_a_source_that_returned_a_malformed_value_cannot_produce_a_nonce(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The result is validated, not trusted."""
    monkeypatch.setattr(
        "mars777_police.protocol.secure_nonce.secrets.token_hex", lambda size: "NOT-HEX"
    )
    with pytest.raises(InvalidNonceError):
        SecretsNonceSource().fresh()


def test_successive_nonces_are_not_the_same_value() -> None:
    """A weak check on purpose: the strong claim is CSPRNG provenance, above."""
    source = SecretsNonceSource()
    assert len({source.fresh().value for _ in range(64)}) == 64


def test_the_scripted_source_is_a_test_seam_not_a_second_implementation() -> None:
    source = ScriptedNonces(["0" * 32, "1" * 32])
    assert source.fresh().value == "0" * 32
    assert source.fresh().value == "1" * 32
    assert source.calls == 2
