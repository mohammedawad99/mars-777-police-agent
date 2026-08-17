"""The gate every outgoing hint passes, and the one prohibition it enforces.

App E #26 requires free natural language and #27 forbids a **direct
numeric-position protocol**. Those are two different rules, and the second one
is narrower than it first looks: it bans a coordinate channel, not arithmetic.
"I checked 3 corridors" is a sentence; `(3,4)` is a protocol. A validator that
could not tell them apart would enforce a rule the source never wrote and would
make ordinary speech unsayable.

`hint_max_words` is NEGOTIABLE with a floor of 1 (App F T14 #2), so the cap
under test is whatever a series locked - never the default 15.
"""

import pytest

from mars777_police.app.hint_validator import (
    HintRejection,
    counted_words,
    normalised,
    validate_hint,
)

CAP = 15
"""A roomy cap, so a case that fails here failed for its own reason."""


def test_the_normal_form_is_nfc() -> None:
    """Two spellings of the same character validate to one text, so two OSes agree."""
    composed, decomposed = "café", "café"

    assert composed != decomposed
    assert normalised(decomposed) == normalised(composed)
    assert validate_hint(decomposed, CAP).text == validate_hint(composed, CAP).text


def test_words_are_counted_by_unicode_whitespace() -> None:
    """One documented rule: normalise, strip, `str.split()`, count."""
    assert counted_words("I chose a legal action") == 5
    assert counted_words("  spaced   out \t words \n here ") == 4
    assert counted_words("") == 0
    assert counted_words("   ") == 0


def test_an_empty_candidate_is_refused() -> None:
    for candidate in ("", "   ", "\t\n"):
        outcome = validate_hint(candidate, CAP)
        assert not outcome.accepted
        assert outcome.reason is HintRejection.EMPTY
        assert outcome.text is None


@pytest.mark.parametrize("cap", [1, 2, 3, 5, 15])
def test_an_accepted_hint_never_exceeds_the_locked_cap(cap: int) -> None:
    """The cap is the locked one, whatever it is - nothing here knows 15."""
    outcome = validate_hint("I chose a legal action", cap)

    if outcome.accepted:
        assert outcome.text is not None
        assert counted_words(outcome.text) <= cap
    else:
        assert outcome.reason is HintRejection.OVER_WORD_LIMIT


def test_a_hint_over_the_cap_is_refused_with_that_reason() -> None:
    outcome = validate_hint("one two three four", 3)

    assert not outcome.accepted
    assert outcome.reason is HintRejection.OVER_WORD_LIMIT


ORDINARY = (
    "I checked 3 corridors",
    "I will wait 2 turns",
    "There are 4 doors",
    "Two of us walked 12 paces",
    "I moved 1 square north",
    "The corridor was 0.9 wide",
)
"""Numbers used as language. App E #27 bans a protocol, not arithmetic."""


@pytest.mark.parametrize("candidate", ORDINARY)
def test_ordinary_numeric_prose_is_accepted(candidate: str) -> None:
    outcome = validate_hint(candidate, CAP)

    assert outcome.accepted, outcome.reason
    assert outcome.text == candidate


COORDINATES = (
    "(3,4)",
    "[3,4]",
    "3,4",
    "3:4",
    "3 / 4",
    "3 4",
    "x=3 y=4",
    "x 3 y 4",
    "row 3 col 4",
    "r=3 c=4",
    "I am at (3,4)",
    "meet me row 3 col 4",
    "X=3 Y=4",
)
"""The forms Detector V1 is required to refuse, from the supervising ruling."""


@pytest.mark.parametrize("candidate", COORDINATES)
def test_direct_coordinate_syntax_is_refused(candidate: str) -> None:
    outcome = validate_hint(candidate, CAP)

    assert not outcome.accepted
    assert outcome.reason is HintRejection.NUMERIC_POSITION
    assert outcome.text is None


def test_two_bare_integers_are_a_coordinate_but_a_sentence_is_not() -> None:
    """Rule 2 is about a payload that *is* a pair, not one that contains numbers."""
    assert validate_hint("3 4", CAP).reason is HintRejection.NUMERIC_POSITION
    assert validate_hint("3 corridors", CAP).accepted
    assert validate_hint("I saw 3 and 4 doors", CAP).accepted


def test_a_single_labelled_number_is_not_a_pair() -> None:
    """One coordinate is not a position; only a pair encodes one."""
    assert validate_hint("row 3 looked empty", CAP).accepted


def test_a_refusal_never_echoes_the_candidate() -> None:
    """A reason code, never the text - a rejected hint may still be ours to keep."""
    secret = "x=7 y=9"
    outcome = validate_hint(secret, CAP)

    assert outcome.text is None
    assert secret not in repr(outcome)
    assert outcome.reason is not None
    assert secret not in outcome.reason.value


def test_validation_is_a_value_and_never_raises_into_the_turn() -> None:
    """The turn path gets an answer, not an exception, for every input."""
    for candidate in ("", "x=1 y=2", "one two three", "fine"):
        assert validate_hint(candidate, 2) is not None
