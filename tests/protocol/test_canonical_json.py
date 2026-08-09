"""Canonical JSON bytes for hashed payloads (Stage 4E-R9-RESUME).

`protocol.canonical` owns bytes, not meaning. It never sees a `SealedState`, a
`PhysicalAction` or a digest - only JSON-native material a caller already mapped
explicitly - which is why its runtime domain is deliberately narrow: `str`,
`int`, `list`, `dict` and nothing else.

The exclusions are the point. Sealed commitment records contain no `float`, no
`null` and no `bool`, so this first canonical implementation refuses them rather
than guessing at rules the wider contract only freezes for other artifacts. And
a non-NFC string arriving here means a producer skipped `canonical_text`; that
is a defect worth surfacing, not one worth silently repairing one step before
hashing.
"""

import json

import pytest

from mars777_police.protocol.canonical import canonical_json_bytes

DECOMPOSED = "e\u0301"
COMPOSED = "\u00e9"

RECORD: dict[str, object] = {
    "hint": "barrier",
    "intent": "lie",
    "move": {"kind": "BARRIER", "value": [5, 6]},
    "nonce": "a" * 32,
    "role": "police",
    "state": {
        "barriers": [[0, 0]],
        "config_sha256": "1" * 64,
        "role": "police",
        "self_pos": [3, 4],
        "step": 3,
    },
    "step": 3,
    "sub_game": 1,
}


def test_the_nested_sealed_record_shape_is_accepted() -> None:
    raw = canonical_json_bytes(RECORD)
    assert isinstance(raw, bytes)
    assert json.loads(raw.decode("utf-8")) == RECORD


def test_keys_are_sorted_and_separators_are_compact() -> None:
    text = canonical_json_bytes(RECORD).decode("utf-8")
    assert text.startswith('{"hint":"barrier","intent":"lie","move":{"kind":"BARRIER"')
    assert ", " not in text and ": " not in text
    assert text == json.dumps(RECORD, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def test_there_is_no_trailing_newline_and_no_pretty_printing() -> None:
    """A stray newline is invisible in a diff and fatal to byte-identity."""
    raw = canonical_json_bytes(RECORD)
    assert not raw.endswith(b"\n") and not raw.endswith(b"\r\n")
    assert b"\n" not in raw and b"\r" not in raw and b"    " not in raw


def test_non_ascii_is_emitted_as_literal_utf8_not_escaped() -> None:
    raw = canonical_json_bytes({"hint": "שלום"})
    assert "שלום".encode() in raw
    assert b"\\u05" not in raw
    assert raw == '{"hint":"שלום"}'.encode()


@pytest.mark.parametrize(
    "value",
    [
        None,
        True,
        False,
        1.0,
        0.5,
        b"bytes",
        bytearray(b"x"),
        ("a",),
        {"a"},
        frozenset({"a"}),
        (x for x in "a"),
        object(),
        range(2),
    ],
)
def test_a_value_outside_the_sealed_record_domain_is_refused(value: object) -> None:
    """`float`/`null`/`bool` never occur in a sealed record, so v1 refuses them."""
    with pytest.raises(ValueError):
        canonical_json_bytes(value)
    with pytest.raises(ValueError):
        canonical_json_bytes({"k": value})
    with pytest.raises(ValueError):
        canonical_json_bytes([value])


@pytest.mark.parametrize("key", [1, None, True, ("a",), 2.0])
def test_a_dict_key_that_is_not_an_exact_str_is_refused(key: object) -> None:
    with pytest.raises(ValueError):
        canonical_json_bytes({key: "v"})


def test_subclasses_of_the_accepted_kinds_are_refused() -> None:
    class Loud(str): ...

    class Big(int): ...

    class Listy(list[object]): ...

    class Mappy(dict[str, object]): ...

    for bad in (Loud("x"), Big(1), Listy([1]), Mappy({"a": 1})):
        with pytest.raises(ValueError):
            canonical_json_bytes(bad)


def test_a_non_nfc_string_is_refused_rather_than_quietly_normalised() -> None:
    """Reaching here un-normalised means a producer skipped `canonical_text`."""
    with pytest.raises(ValueError):
        canonical_json_bytes(DECOMPOSED)
    with pytest.raises(ValueError):
        canonical_json_bytes({"hint": DECOMPOSED})
    with pytest.raises(ValueError):
        canonical_json_bytes({DECOMPOSED: "v"})
    assert canonical_json_bytes({"hint": COMPOSED}) == '{"hint":"é"}'.encode()


def test_the_module_neither_hashes_nor_knows_any_semantic_type() -> None:
    from mars777_police.protocol import canonical

    for forbidden in ("hashlib", "hmac", "secrets", "SealedState", "Sha256Digest", "NonceValue"):
        assert not hasattr(canonical, forbidden)
