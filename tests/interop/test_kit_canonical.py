"""The KIT canonical form, beside ours rather than instead of it.

Two canonical authorities exist on purpose. `protocol.canonical` serves the
**strict project domain**: it refuses `None` and binary `float`, carries
decimals as exact text, and is what every existing project hash is computed
over. `protocol.kit_canonical` serves the **KIT external profile**: the
JSON-native domain the pinned kit actually uses, floats included, so a peer's
bytes can be reproduced exactly as that peer produced them.

Neither may drift into the other. A permissive single function would silently
let a binary float reach a strict project hash, which is the one thing the
decimal-as-text design exists to prevent.
"""

import pytest
from kit_vectors import CANONICAL, FLOATS

from mars777_police.protocol.kit_canonical import kit_canonical_bytes, kit_canonical_text


@pytest.mark.parametrize(("value", "expected"), CANONICAL)
def test_the_shared_domain_reproduces_the_kit_bytes(value: object, expected: str) -> None:
    assert kit_canonical_text(value) == expected
    assert kit_canonical_bytes(value) == expected.encode("utf-8")


@pytest.mark.parametrize(("value", "expected"), FLOATS)
def test_binary_floats_render_as_the_kit_renders_them(value: object, expected: str) -> None:
    """Python's shortest round-trip repr, exponent forms and all."""
    assert kit_canonical_text(value) == expected


def test_the_strict_project_authority_still_refuses_what_it_always_refused() -> None:
    """Adding KIT support must not widen the strict domain by one type."""
    from mars777_police.protocol.canonical import canonical_json_bytes

    for refused in ({"b": None}, {"x": 1.5}):
        with pytest.raises(ValueError):
            canonical_json_bytes(refused)


def test_the_two_authorities_agree_wherever_both_accept() -> None:
    """Where the domains overlap the bytes are identical - one convention, two doors."""
    from mars777_police.protocol.canonical import canonical_json_bytes

    shared = {"a": {"c": 3, "d": 4}, "b": 1, "hint": "אני ליד הכיכר 🙂"}

    assert kit_canonical_bytes(shared) == canonical_json_bytes(shared)


def test_it_refuses_a_value_outside_the_json_domain() -> None:
    """Only JSON-native values: no dates, no sets, no arbitrary objects."""
    with pytest.raises(ValueError):
        kit_canonical_bytes({"when": object()})


def test_a_non_string_object_key_is_refused() -> None:
    """JSON object keys are strings; `json.dumps` would coerce, which changes bytes."""
    with pytest.raises(ValueError, match="keys must be str"):
        kit_canonical_bytes({1: "one"})
