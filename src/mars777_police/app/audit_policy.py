"""Whether a reviewed sub-game may be called counted-clean, decided once.

Two opposite mistakes are being prevented, which is why this is one authority
rather than a rule repeated at each call site. Treating an undecidable
**binding** question as clean would score a peer as having proved something
nobody checked. Treating an undecidable **enrichment** question as a violation
would accuse a lawful peer of cheating for using a leaner payload than ours.

**Absence and contradiction are reported separately.** `blocking` says the
result may not be called counted-clean; `violations` says evidence positively
contradicts the peer. An undecided binding check appears in the first and never
in the second - it is a gap in what we can prove, not an accusation, and a
report that conflated them would libel an honest opponent.

An empty review is refused outright: nothing checked is not everything passed,
and a caller that reviewed no checks has a defect this would otherwise hide.
"""

from dataclasses import dataclass

from .audit_status import CheckProvenance, CheckStatus

BLOCKING_PROVENANCE = (CheckProvenance.SOURCE_BINDING, CheckProvenance.PROFILE_REQUIRED)
"""The tiers whose unanswered questions cost a counted result."""


@dataclass(frozen=True, slots=True)
class CheckOutcome:
    """One named semantic check, its authority, and what it concluded."""

    name: str
    provenance: CheckProvenance
    status: CheckStatus


@dataclass(frozen=True, slots=True)
class CountedVerdict:
    """Whether the review supports a counted result, and precisely why not."""

    clean: bool
    blocking: tuple[str, ...]
    violations: tuple[str, ...]


def counted_clean(outcomes: tuple[CheckOutcome, ...]) -> CountedVerdict:
    """Judge *outcomes* against the provenance rules, naming every obstacle."""
    if not outcomes:
        raise ValueError("a counted verdict needs at least one check to judge")
    violations = tuple(one.name for one in outcomes if one.status.violated)
    blocking = tuple(
        one.name
        for one in outcomes
        if one.status.violated
        or (one.status is CheckStatus.NOT_CHECKABLE and one.provenance in BLOCKING_PROVENANCE)
    )
    return CountedVerdict(clean=not blocking, blocking=blocking, violations=violations)
