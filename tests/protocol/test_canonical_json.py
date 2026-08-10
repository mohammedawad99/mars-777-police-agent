"""Canonical JSON bytes for hashed payloads (Stage 4E-R9-RESUME).

`protocol.canonical` owns bytes, not meaning. It never sees a `SealedState`, a
`PhysicalAction` or a digest - only JSON-native material a caller already mapped
explicitly - which is why its runtime domain is deliberately narrow.

The exclusions are the point, and they are still exact. `float` and `null` are
refused: `0.10` has no `float` spelling, so binary rounding could perturb hashed
bytes, and a hashed payload omits an absent member rather than emitting `null`.
`bool` and `Decimal` were refused with them until Stage 4E-R16, when the Step-0
and config cores first needed the two forms `CANONICALIZATION_CONTRACT.md` had
already frozen; `test_canonical_decimals.py` asserts those, and this file keeps
fixing everything the sealed-record path depends on. A non-NFC string arriving
here still means a producer skipped `canonical_text` - a defect worth surfacing,
not one worth silently repairing one step before hashing.
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
def test_a_value_outside_the_canonical_domain_is_refused(value: object) -> None:
    """`float` and `null` are still refused, at every depth."""
    with pytest.raises(ValueError):
        canonical_json_bytes(value)
    with pytest.raises(ValueError):
        canonical_json_bytes({"k": value})
    with pytest.raises(ValueError):
        canonical_json_bytes([value])


def test_no_sealed_record_member_may_be_a_bool_or_a_decimal() -> None:
    """The domain grew; the sealed record did not.

    Stage 4E-R16 admitted `bool` and `Decimal` for the Step-0 and config cores.
    None of the eight sealed members is either one - `step` and `sub_game` are
    integers, the rest are strings or the mapped `state`/`move` objects - so
    this record stays exactly what it was, and its bytes with it.
    """
    for value in RECORD.values():
        assert type(value) is not bool
        assert type(value).__name__ != "Decimal"
    assert (
        canonical_json_bytes(RECORD)
        == json.dumps(RECORD, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    )


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
