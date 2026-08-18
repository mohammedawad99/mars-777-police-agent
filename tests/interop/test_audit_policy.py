"""Whether a series may be called counted-clean, decided in exactly one place.

Two failure modes are being prevented at once, and they pull in opposite
directions. Treating an undecidable **binding** question as clean would let a
peer that disclosed too little be scored as if it had proved everything.
Treating an undecidable **project-enrichment** question as tampering would
accuse a lawful peer of cheating for using a leaner payload than ours.

So provenance decides what an undecided check means, and the answer lives here
rather than being re-derived at each call site.
"""

import pytest

from mars777_police.app.audit_policy import CheckOutcome, counted_clean
from mars777_police.app.audit_status import CheckProvenance, CheckStatus

BINDING = CheckProvenance.SOURCE_BINDING
PROFILE = CheckProvenance.PROFILE_REQUIRED
EXTRA = CheckProvenance.PROJECT_ENRICHMENT


def outcome(name: str, provenance: CheckProvenance, status: CheckStatus) -> CheckOutcome:
    return CheckOutcome(name=name, provenance=provenance, status=status)


def test_all_binding_checks_verified_is_clean() -> None:
    assert counted_clean(
        (
            outcome("trajectory", BINDING, CheckStatus.VERIFIED),
            outcome("legality", BINDING, CheckStatus.VERIFIED),
        )
    ).clean


def test_a_failed_binding_check_is_not_clean() -> None:
    verdict = counted_clean((outcome("legality", BINDING, CheckStatus.FAILED),))

    assert not verdict.clean
    assert "legality" in verdict.blocking


def test_an_undecidable_binding_check_blocks_without_accusing() -> None:
    """The central rule: unknown is not clean, and unknown is not cheating."""
    verdict = counted_clean((outcome("capture", BINDING, CheckStatus.NOT_CHECKABLE),))

    assert not verdict.clean
    assert "capture" in verdict.blocking
    assert not verdict.violations


def test_an_undecidable_profile_check_also_blocks() -> None:
    verdict = counted_clean((outcome("scent", PROFILE, CheckStatus.NOT_CHECKABLE),))

    assert not verdict.clean
    assert not verdict.violations


def test_an_undecidable_enrichment_check_neither_blocks_nor_accuses() -> None:
    """A leaner lawful payload must not cost a peer its result."""
    verdict = counted_clean(
        (
            outcome("trajectory", BINDING, CheckStatus.VERIFIED),
            outcome("our-own-extra", EXTRA, CheckStatus.NOT_CHECKABLE),
        )
    )

    assert verdict.clean
    assert not verdict.violations


def test_a_failed_enrichment_check_is_still_a_violation() -> None:
    """Contradictory evidence is a finding whatever tier it came from."""
    verdict = counted_clean((outcome("our-own-extra", EXTRA, CheckStatus.FAILED),))

    assert not verdict.clean
    assert "our-own-extra" in verdict.violations


def test_not_applicable_never_blocks_at_any_provenance() -> None:
    for provenance in (BINDING, PROFILE, EXTRA):
        verdict = counted_clean((outcome("n/a", provenance, CheckStatus.NOT_APPLICABLE),))
        assert verdict.clean


def test_absence_of_evidence_is_reported_separately_from_contradiction() -> None:
    verdict = counted_clean(
        (
            outcome("undecided", BINDING, CheckStatus.NOT_CHECKABLE),
            outcome("broken", BINDING, CheckStatus.FAILED),
        )
    )

    assert set(verdict.blocking) == {"undecided", "broken"}
    assert set(verdict.violations) == {"broken"}


def test_an_empty_review_is_not_evidence_of_cleanliness() -> None:
    """Nothing checked is not the same as everything passed."""
    with pytest.raises(ValueError, match="at least one check"):
        counted_clean(())
