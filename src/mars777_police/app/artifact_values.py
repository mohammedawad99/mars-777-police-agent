"""Immutable primitives shared by more than one official artifact.

Two values live here because the **declaration** and the **result** both need
them, and duplicating either would create two authoritative spellings of one
semantic fact (`MODULE_BOUNDARIES.md`, Stage 4E-R14-R1/FIX). The module is
cohesive by exactly that test and must not accumulate unrelated types.

**Representation only.** Nothing here reads a clock, touches Git, serializes,
canonicalizes or hashes: a value proves how a string is *written*, never that it
names a real commit or a real instant.
"""

from dataclasses import dataclass
from typing import Final

GIT_COMMIT_SHA_LENGTH: Final[int] = 40
"""Characters in a Git commit id written in hexadecimal (SHA-1 width)."""

UTC_TIMESTAMP_LENGTH: Final[int] = 20
"""Characters in ``YYYY-MM-DDTHH:MM:SSZ``."""

_HEX_DIGITS: Final[frozenset[str]] = frozenset("0123456789abcdef")
"""The lowercase hexadecimal alphabet; uppercase is deliberately absent."""

_DIGITS: Final[frozenset[str]] = frozenset("0123456789")

_TIMESTAMP_LITERALS: Final[tuple[tuple[int, str], ...]] = (
    (4, "-"),
    (7, "-"),
    (10, "T"),
    (13, ":"),
    (16, ":"),
    (19, "Z"),
)
"""Index -> required literal character in the frozen lexical form."""


class InvalidGitCommitShaError(ValueError):
    """Raised when a string is not the locked Git commit representation."""


class InvalidUtcTimestampError(ValueError):
    """Raised when a string is not the locked UTC timestamp representation."""


@dataclass(frozen=True, slots=True)
class GitCommitSha:
    """A validated textual Git commit id: exactly 40 lowercase hex characters.

    `DECLARATION_CONTRACT.md` types ``teams.<g>.github_commit`` as 40-hex and
    every live example is lowercase, so one spelling is accepted and another is
    **refused, never normalised** - the same discipline ``Sha256Digest`` applies.
    It is a *version identity*, never authentication (`PRD06-FR-030`).
    """

    value: str

    def __post_init__(self) -> None:
        if type(self.value) is not str:
            raise InvalidGitCommitShaError(
                f"git commit must be a str, got {type(self.value).__name__}",
            )
        if len(self.value) != GIT_COMMIT_SHA_LENGTH:
            raise InvalidGitCommitShaError(
                f"git commit must be exactly {GIT_COMMIT_SHA_LENGTH} characters,"
                f" got {len(self.value)}",
            )
        if not _HEX_DIGITS.issuperset(self.value):
            raise InvalidGitCommitShaError(
                "git commit must be lowercase hexadecimal; uppercase, whitespace"
                " and prefixes are refused, never normalised",
            )


@dataclass(frozen=True, slots=True)
class UtcTimestamp:
    """A validated instant in the one frozen lexical form ``YYYY-MM-DDTHH:MM:SSZ``.

    Exactly 20 ASCII characters, second precision, literal ``T`` and ``Z``; no
    fractional seconds, no offset, no whitespace and no alternate spelling. The
    form is pinned because the value is **hashed and echoed verbatim** - two
    spellings of one instant would produce different canonical bytes.

    **Lexical validation only, deliberately.** No current contract freezes
    calendar validity, so none is invented here: a lexically valid but
    calendar-impossible string is a producer defect caught elsewhere, exactly as
    ``NonceValue`` accepts ``"0" * 32``. This value also never reads a clock -
    obtaining the instant is the proposer's runtime duty.
    """

    value: str

    def __post_init__(self) -> None:
        if type(self.value) is not str:
            raise InvalidUtcTimestampError(
                f"timestamp must be a str, got {type(self.value).__name__}",
            )
        if len(self.value) != UTC_TIMESTAMP_LENGTH:
            raise InvalidUtcTimestampError(
                f"timestamp must be exactly {UTC_TIMESTAMP_LENGTH} characters,"
                f" got {len(self.value)}",
            )
        for index, literal in _TIMESTAMP_LITERALS:
            if self.value[index] != literal:
                raise InvalidUtcTimestampError(
                    f"timestamp must carry {literal!r} at index {index};"
                    " the lexical form YYYY-MM-DDTHH:MM:SSZ is exact",
                )
        digits = "".join(
            self.value[start:stop]
            for start, stop in ((0, 4), (5, 7), (8, 10), (11, 13), (14, 16), (17, 19))
        )
        if not _DIGITS.issuperset(digits):
            raise InvalidUtcTimestampError(
                "timestamp date and time components must be ASCII digits;"
                " whitespace, signs and fractional seconds are refused",
            )
