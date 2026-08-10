"""The Stage-4E-R16 canonical domain extension: `bool` and `Decimal`.

The v1 module refused both, correctly, because a sealed commitment record
contains neither. A payload now needs them - `hardware.gpu` is `string | False`
and the config core carries two FIXED decimals - so the domain grew to exactly
what `CANONICALIZATION_CONTRACT.md` already froze, and no further.

`0.10` is the test that matters. It has no `float` spelling, so a serializer
that reached for `float` would emit `0.1`, change the bytes, and make two honest
peers disagree on `config_sha256`.
"""

from decimal import Decimal

import pytest

from mars777_police.protocol.canonical import canonical_json_bytes, decimal_text


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (Decimal("0.9"), b"0.9"),
        (Decimal("0.10"), b"0.10"),
        (Decimal("0"), b"0"),
        (Decimal("35"), b"35"),
        (Decimal("3.50"), b"3.50"),
        (Decimal("-1.5"), b"-1.5"),
    ],
)
def test_a_decimal_is_emitted_verbatim_as_a_json_number(value: Decimal, expected: bytes) -> None:
    assert canonical_json_bytes({"k": value}) == b'{"k":' + expected + b"}"


def test_trailing_zeros_are_significant_and_never_normalised() -> None:
    """`0.10` and `0.1` are the same quantity and deliberately different bytes."""
    assert canonical_json_bytes(Decimal("0.10")) != canonical_json_bytes(Decimal("0.1"))


def test_several_decimals_in_one_payload_each_substitute_exactly_once() -> None:
    payload = {"a": Decimal("0.9"), "b": Decimal("0.10"), "c": [Decimal("1.0")]}
    assert canonical_json_bytes(payload) == b'{"a":0.9,"b":0.10,"c":[1.0]}'


def test_booleans_are_emitted_as_json_literals() -> None:
    assert canonical_json_bytes({"gpu": False}) == b'{"gpu":false}'
    assert canonical_json_bytes({"gpu": True}) == b'{"gpu":true}'


def test_a_bool_is_not_silently_an_int() -> None:
    assert canonical_json_bytes({"k": True}) != canonical_json_bytes({"k": 1})


@pytest.mark.parametrize("value", [1.0, 0.5, None, b"x", object()])
def test_float_and_null_stay_outside_the_domain(value: object) -> None:
    """`float` is refused because `0.10` has no exact binary spelling."""
    with pytest.raises(ValueError):
        canonical_json_bytes({"k": value})


def test_an_exponent_or_infinite_decimal_is_refused_rather_than_reformatted() -> None:
    for bad in (Decimal("Infinity"), Decimal("-Infinity"), Decimal("NaN")):
        with pytest.raises(ValueError):
            canonical_json_bytes({"k": bad})


def test_negative_zero_is_refused_and_never_normalised_to_zero() -> None:
    with pytest.raises(ValueError):
        decimal_text(Decimal("-0"))
    with pytest.raises(ValueError):
        canonical_json_bytes({"k": Decimal("-0.0")})


def test_a_large_exponent_decimal_becomes_positional_text() -> None:
    assert decimal_text(Decimal("1E+2")) == "100"
    assert canonical_json_bytes({"k": Decimal("1E+2")}) == b'{"k":100}'


def test_a_payload_that_spells_a_generated_placeholder_is_refused() -> None:
    """Fail closed on a collision rather than silently mis-substituting."""
    with pytest.raises(ValueError):
        canonical_json_bytes({"a": Decimal("1"), "b": "\ue000d0\ue000"})


def test_the_placeholder_mark_is_ordinary_data_when_no_decimal_is_present() -> None:
    """No substitution runs, so nothing can collide and nothing is rewritten."""
    assert canonical_json_bytes({"k": "\ue000d0\ue000"}) == '{"k":"\ue000d0\ue000"}'.encode()


def test_a_decimal_key_is_still_refused() -> None:
    with pytest.raises(ValueError):
        canonical_json_bytes({Decimal("1"): "v"})


def test_the_extension_did_not_disturb_the_sealed_record_shape() -> None:
    record = {"step": 7, "role": "police", "barriers": [[0, 1]], "hint": "x"}
    assert canonical_json_bytes(record) == (
        b'{"barriers":[[0,1]],"hint":"x","role":"police","step":7}'
    )
