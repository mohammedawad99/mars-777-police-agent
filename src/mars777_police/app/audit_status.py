"""What a semantic check concluded - and the difference three of these carry.

A check that **passed** and a check that **could not be decided** are different
facts about the world, and collapsing them fails in both directions at once.
Read as a pass, an undecidable binding question makes a peer that disclosed too
little look like it proved everything. Read as a failure, it accuses a lawful
peer of cheating for carrying a leaner payload than ours. Neither is a verdict
anyone should be able to reach by accident, so undecided is its own value.

**Truthiness is deliberately not defined.** `Optional[bool]` would have made
`if status:` read as "passed", and `NOT_CHECKABLE` would then have answered yes
to a question nobody could answer. Callers ask `.passed` or `.violated`, and
both are `False` for an undecided check - which is the honest pair of answers.

**Provenance decides what undecided *means*.** A source-binding question that
cannot be settled blocks a counted result; one of our own enrichments that
cannot be settled costs nothing, because the peer never agreed to provide it.
That policy lives in `audit_policy`; this module only names the vocabulary.
"""

from enum import StrEnum


class CheckStatus(StrEnum):
    """The four things a semantic check can conclude."""

    VERIFIED = "VERIFIED"
    """Evidence exists and the check passed."""

    FAILED = "FAILED"
    """Evidence exists and proves a violation."""

    NOT_APPLICABLE = "NOT_APPLICABLE"
    """The check does not apply to this turn, outcome or profile."""

    NOT_CHECKABLE = "NOT_CHECKABLE"
    """The check applies, but this lawful profile cannot decide it."""

    @property
    def passed(self) -> bool:
        """Whether the check actually established what it set out to."""
        return self is CheckStatus.VERIFIED

    @property
    def violated(self) -> bool:
        """Whether evidence positively contradicts the expected behaviour."""
        return self is CheckStatus.FAILED


class CheckProvenance(StrEnum):
    """Where a check's authority comes from, which is what undecided costs."""

    SOURCE_BINDING = "SOURCE_BINDING"
    """The course book requires it; unknown blocks a counted result."""

    PROFILE_REQUIRED = "PROFILE_REQUIRED"
    """The mutually frozen profile promised it; unknown blocks too."""

    PROJECT_ENRICHMENT = "PROJECT_ENRICHMENT"
    """Ours alone. A peer never agreed to supply it, so absence costs nothing."""
