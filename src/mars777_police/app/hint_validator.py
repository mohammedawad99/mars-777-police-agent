"""The gate every outgoing hint passes before it can be sealed.

App E #26 and #27 are two different rules and the second is the narrower one:
free natural language is required, and what is forbidden is a **direct
numeric-position protocol** - a coordinate channel, not arithmetic. "I checked
3 corridors" is a sentence; `(3,4)` is a protocol. A blanket digit ban would
enforce a rule the source never wrote and would make ordinary speech unsayable,
so Detector V1 refuses only coordinate *syntax* and is deliberately small
enough to read.

Three forms are refused, and nothing else:

* a pair joined by an explicit separator - `(3,4)`, `[3,4]`, `3,4`, `3:4`,
  `3 / 4`;
* a payload that **is** a pair - two bare integers and nothing else, `3 4`;
* two labelled coordinates - `x=3 y=4`, `x 3 y 4`, `row 3 col 4`, `r=3 c=4`.

One accepted false positive is recorded rather than hidden: a clock time such
as `12:30` matches the separator form. The supervising ruling names `3:4`
explicitly, and refusing a hint that could have said "half past twelve" costs a
sentence, while inferring intent from the numbers would be the NLP this
detector must not become.

**A rejection is a value, never an exception.** The turn path asks a question
and gets an answer; a hint that cannot be sent is replaced by its owner rather
than aborting a lawful turn. The answer carries a reason **code** and never the
candidate text, so a refused hint is not copied into a log line by accident.
"""

import re
import unicodedata
from dataclasses import dataclass
from enum import StrEnum
from typing import Final


class HintRejection(StrEnum):
    """Why a candidate may not be sent. Three reasons, and no free text."""

    EMPTY = "empty"
    OVER_WORD_LIMIT = "over_word_limit"
    NUMERIC_POSITION = "numeric_position"


@dataclass(frozen=True, slots=True)
class HintValidation:
    """The verdict on one candidate: the text to send, or the reason not to."""

    accepted: bool
    text: str | None
    reason: HintRejection | None


_SEPARATED: Final = re.compile(
    r"[(\[]\s*\d+\s*[,:/]\s*\d+\s*[)\]]"  # (3,4)  [3,4]
    r"|(?<!\S)\d+\s*[,:/]\s*\d+(?!\S)"  # 3,4   3:4   3 / 4
)
"""A coordinate pair joined by an explicit separator, bracketed or bare."""

_LABELLED: Final = re.compile(
    r"\b(?:x|y|r|c|row|rows|col|cols|column|columns)\b\s*[=:]?\s*\d+",
    re.IGNORECASE,
)
"""One labelled coordinate. Two of them in one hint make a position."""


def normalised(text: str) -> str:
    """Unicode NFC, then surrounding whitespace removed - and nothing else.

    NFC is the same normal form `protocol.canonical` already requires of every
    canonical string, so a hint that is sealed is a hint that was validated in
    the form it will be hashed in. No case folding and no internal rewriting:
    what is sent is what was written.
    """
    return unicodedata.normalize("NFC", text).strip()


def counted_words(text: str) -> int:
    """The word count, by one documented rule: normalise, then `str.split()`.

    `str.split()` with no argument splits on Unicode whitespace and discards
    runs of it, which is deterministic, locale-independent and identical on
    Linux and Windows. No regular expression and no tokenizer: those are where
    two platforms quietly disagree.
    """
    return len(normalised(text).split())


def encodes_position(text: str) -> bool:
    """Whether *text* carries a direct numeric position under Detector V1."""
    if _SEPARATED.search(text):
        return True
    tokens = text.split()
    if len(tokens) == 2 and all(token.isdigit() for token in tokens):
        return True
    return len(_LABELLED.findall(text)) >= 2


def validate_hint(candidate: str, hint_max_words: int) -> HintValidation:
    """Judge *candidate* against the locked word budget and App E #27.

    The prohibition is checked before the cap so that a coordinate is reported
    as one whatever its length: a hint that both encodes a position and runs
    long is refused for the reason that matters.
    """
    text = normalised(candidate)
    if not text:
        return HintValidation(False, None, HintRejection.EMPTY)
    if encodes_position(text):
        return HintValidation(False, None, HintRejection.NUMERIC_POSITION)
    if len(text.split()) > hint_max_words:
        return HintValidation(False, None, HintRejection.OVER_WORD_LIMIT)
    return HintValidation(True, text, None)
