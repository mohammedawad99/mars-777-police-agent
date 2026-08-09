"""Canonical text normalisation (Stage 4E-R9-RESUME).

PRD06-FR-003 requires text to be Unicode NFC before encoding, and that is the
whole of this contract: no trim, no case fold, no translation. NFC matters
because the hint is free natural-language text - a Hebrew or accented hint typed
on two different machines can carry the same characters in different codepoint
sequences, which hash to different bytes and would report a false TAMPERED.

The JSON-bytes half lives in `test_canonical_json.py`.
"""

import unicodedata

import pytest

from mars777_police.protocol.canonical import canonical_text

DECOMPOSED = "é"
COMPOSED = "é"


def test_canonical_text_composes_a_decomposed_sequence() -> None:
    assert [hex(ord(c)) for c in DECOMPOSED] == ["0x65", "0x301"]
    assert canonical_text(DECOMPOSED) == COMPOSED
    assert [hex(ord(c)) for c in canonical_text(DECOMPOSED)] == ["0xe9"]


def test_canonical_text_is_idempotent_and_leaves_ascii_alone() -> None:
    assert canonical_text(COMPOSED) == COMPOSED
    assert canonical_text(canonical_text(DECOMPOSED)) == COMPOSED
    assert canonical_text("barrier") == "barrier"
    assert canonical_text("שלום") == "שלום"


@pytest.mark.parametrize("text", ["  padded  ", "MiXeD", "trailing\n", "", "a\tb"])
def test_canonical_text_normalises_only_and_never_trims_or_folds(text: str) -> None:
    """NFC and nothing else - no strip, no case change, no translation."""
    assert canonical_text(text) == unicodedata.normalize("NFC", text) == text


@pytest.mark.parametrize("value", [None, True, 1, 1.0, b"x", ["x"], ("x",), {"x": 1}])
def test_canonical_text_refuses_anything_that_is_not_an_exact_str(value: object) -> None:
    with pytest.raises(ValueError):
        canonical_text(value)  # type: ignore[arg-type]


def test_canonical_text_refuses_a_str_subclass() -> None:
    class Loud(str): ...

    with pytest.raises(ValueError):
        canonical_text(Loud("x"))
