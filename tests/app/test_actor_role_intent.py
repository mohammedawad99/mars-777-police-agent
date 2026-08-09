"""The two closed sealed-record vocabularies (Stage 4E-R9-R2).

`intent` is **source law**: Ch 5 §5.3.1 (p.51) defines the flag as saying whether
the accompanying hint is true *(truth)* or misleading *(lie)*, printing both
English words inside the Hebrew prose. `role` is **PROJECT-CONTRACT** (Stage
4E-R9-R1): the book labels the sides only as *Cop* / *Thief* in Figure 6, which
is explanatory terminology and never a byte string, so a canonical spelling had
to be chosen and `police`/`thief` was frozen.

Three vocabularies now coexist deliberately - source `Cop`/`Thief`, sealed
`police`/`thief`, and the PRD-01 score keys `cop`/`thief` - so most of this file
exists to stop them collapsing into one another. The runtime→sealed mapping
(`"POLICE"` → `"police"`) is a *future producer* duty and is deliberately absent
here: this stage only proves the destination vocabulary exists.
"""

import enum

import pytest

from mars777_police import ROLE, VALID_ROLES
from mars777_police.app.sealed_record_values import ActorRole, Intent


def test_the_role_vocabulary_is_exactly_two_members() -> None:
    assert list(ActorRole.__members__) == ["POLICE", "THIEF"]
    assert [role.value for role in ActorRole] == ["police", "thief"]


def test_the_intent_vocabulary_is_exactly_two_members() -> None:
    assert list(Intent.__members__) == ["TRUTH", "LIE"]
    assert [intent.value for intent in Intent] == ["truth", "lie"]


def test_each_exact_value_constructs_its_member() -> None:
    assert ActorRole("police") is ActorRole.POLICE
    assert ActorRole("thief") is ActorRole.THIEF
    assert Intent("truth") is Intent.TRUTH
    assert Intent("lie") is Intent.LIE


def test_both_are_str_enums_so_the_codec_can_read_value_directly() -> None:
    """StrEnum because these are closed vocabularies, not formatted strings."""
    assert issubclass(ActorRole, enum.StrEnum)
    assert issubclass(Intent, enum.StrEnum)
    assert ActorRole.POLICE.value == "police"
    assert Intent.LIE.value == "lie"


@pytest.mark.parametrize(
    "text",
    ["POLICE", "THIEF", "Police", "Cop", "cop", "COP", "Thief", "robber", "", " police", "police "],
)
def test_no_other_spelling_is_a_role(text: str) -> None:
    """`Cop` is the book's display word and `cop` is a score key - neither seals."""
    with pytest.raises(ValueError, match="is not a valid ActorRole"):
        ActorRole(text)


@pytest.mark.parametrize(
    "text",
    ["TRUTH", "LIE", "Truth", "true", "false", "honest", "deceptive", "neutral", "unknown", ""],
)
def test_no_other_spelling_is_an_intent(text: str) -> None:
    with pytest.raises(ValueError, match="is not a valid Intent"):
        Intent(text)


@pytest.mark.parametrize("value", [True, False, None, 0, 1, 0.0, b"police", b"truth", ["police"]])
def test_no_non_string_is_a_member_of_either_vocabulary(value: object) -> None:
    """A bool is not a truth flag: `intent` is a two-word vocabulary, not a bool."""
    with pytest.raises(ValueError, match="is not a valid"):
        ActorRole(value)  # type: ignore[call-overload]
    with pytest.raises(ValueError, match="is not a valid"):
        Intent(value)  # type: ignore[call-overload]


def test_neither_vocabulary_carries_an_alias_or_a_rescue_hook() -> None:
    """A `_missing_` hook would quietly re-admit every spelling refused above."""
    assert len(ActorRole) == len(ActorRole.__members__) == 2
    assert len(Intent) == len(Intent.__members__) == 2
    for member in ("COP", "ROBBER", "UNKNOWN", "NONE", "BOTH"):
        assert member not in ActorRole.__members__
    for member in ("TRUE", "FALSE", "HONEST", "DECEPTIVE", "UNKNOWN", "NEUTRAL"):
        assert member not in Intent.__members__


def test_neither_vocabulary_serializes_maps_or_infers() -> None:
    """The future codec reads `.value` explicitly; nothing here does it for it."""
    for vocab in (ActorRole, Intent):
        for absent in ("to_json", "serialize", "canonical", "wire_value", "encode_canonical"):
            assert not hasattr(vocab, absent)
    for absent in ("from_runtime_role", "from_role", "of_runtime", "map_runtime"):
        assert not hasattr(ActorRole, absent)
    for absent in ("from_hint", "infer", "of_hint", "classify"):
        assert not hasattr(Intent, absent)


def test_the_module_reaches_no_serialization_or_randomness() -> None:
    from mars777_police.app import sealed_record_values

    for forbidden in ("json", "hashlib", "hmac", "secrets", "random", "os", "uuid", "time"):
        assert not hasattr(sealed_record_values, forbidden)


def test_the_repository_runtime_role_constants_are_untouched_and_distinct() -> None:
    """Runtime identity stays uppercase; mapping to the sealed word is a producer duty."""
    assert ROLE == "POLICE"
    assert set(VALID_ROLES) == {"POLICE", "THIEF"}
    assert ROLE not in {role.value for role in ActorRole}
    assert ActorRole.POLICE.value != ROLE


def test_the_two_vocabularies_never_overlap() -> None:
    assert {role.value for role in ActorRole} & {intent.value for intent in Intent} == set()


def test_both_vocabularies_are_on_the_app_surface() -> None:
    from mars777_police import app
    from mars777_police.app import sealed_record_values

    assert app.ActorRole is sealed_record_values.ActorRole
    assert app.Intent is sealed_record_values.Intent
    assert {"ActorRole", "Intent"} <= set(app.__all__)


def test_neither_vocabulary_leaks_onto_the_peer_message_facade() -> None:
    """They are sealed-record prerequisites, not peer-visible message families."""
    from mars777_police.app import peer_messages

    assert not hasattr(peer_messages, "ActorRole")
    assert not hasattr(peer_messages, "Intent")
