"""A truthful sentence to say while PRD-04 does not exist yet.

Ch 6 §6.5.1 offers four ways to produce the verbal layer and makes the first one
the default: *"[template provider] - **the default**. Pre-written sentences,
selected in Python code - **zero tokens, no network dependency**. This is the
recommended path."* So a fixed sentence chosen by code is the book's own
zero-token mode, not a shortcut around it.

**Temporary, and labelled so.** PRD-04 owns hint generation, bluffing and the
`intent` policy that goes with them. This module exists only so the turn a
driver seals has something lawful in its `hint` member until that lands, and it
should be deleted rather than extended.

**Truthful, therefore `Intent.TRUTH`.** `PeerRunner.open_turn` projects the
emission through `LocalTurnService.apply`, which raises on an action our own
rules refuse - so by the time a hint is sealed beside an action, "I chose a
legal action" is already established. Ch 5 p.51 requires the classification to
be honest even when the text is a bluff; here the text is not a bluff.

**It adapts; it never refuses a config.** `hint_max_words` is NEGOTIABLE (App F
T14 #2) and only its floor of 1 is fixed, so a series may lock a value narrower
than the fullest sentence. Rejecting such a config over a stopgap template would
let this module veto lawful counted play, so it shortens instead. Every rung is
a natural-language sentence with no coordinate in it, because App E #26 requires
free natural language and #27 forbids a numeric-position protocol.
"""

from dataclasses import dataclass

from .sealed_record_values import Intent


@dataclass(frozen=True, slots=True)
class SpokenHint:
    """One turn's verbal half: the text, and how honestly it is meant."""

    text: str
    intent: Intent


def t0_hint(hint_max_words: int) -> SpokenHint:
    """The longest truthful sentence that fits the series' locked word budget.

    Three rungs, because three is what the floor of 1 and the App F default of
    15 actually need. Every one of them says the same true thing, so shortening
    costs meaning rather than honesty.
    """
    if hint_max_words < 1:
        raise ValueError(f"hint_max_words is at least 1 by contract, got {hint_max_words}")
    if hint_max_words >= 5:
        return SpokenHint("I chose a legal action.", Intent.TRUTH)
    if hint_max_words >= 3:
        return SpokenHint("Legal action chosen.", Intent.TRUTH)
    return SpokenHint("Legal.", Intent.TRUTH)
