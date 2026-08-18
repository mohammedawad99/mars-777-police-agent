"""Which authority stands behind each finding this project can report.

The classification is exhaustive on purpose. A finding that nobody classified
would reach the counted-clean policy with no rule attached, and the safe
default in that situation is not obvious - so the matrix is required to name
every verdict the semantic reviewer can produce, and a test fails the build if
a new one appears without a provenance.

The interesting rows are the enrichments. `DISHONEST_SCENT_EMISSION` is ours
under JDEC-018: it needs a disclosed trajectory to re-render an emission from,
and a lawful KIT peer never agreed to disclose one. Absence there must cost
nothing, while a *contradiction* remains a finding at any tier.
"""

from mars777_police.app.audit_provenance import PROVENANCE, provenance_of
from mars777_police.app.audit_status import CheckProvenance
from mars777_police.app.semantic_values import SemanticVerdict


def test_every_semantic_verdict_is_classified() -> None:
    """No verdict may reach the policy without an authority behind it."""
    assert set(PROVENANCE) == set(SemanticVerdict)


def test_the_gameplay_rules_are_source_binding() -> None:
    for verdict in (
        SemanticVerdict.WRONG_START,
        SemanticVerdict.BROKEN_TRAJECTORY,
        SemanticVerdict.ILLEGAL_ACTION,
        SemanticVerdict.WRONG_BARRIER_SET,
        SemanticVerdict.FALSE_CAPTURE_CLAIM,
        SemanticVerdict.DISHONEST_CAPTURE_ANSWER,
        SemanticVerdict.FALSE_CLAIM_AFFIRMED,
    ):
        assert provenance_of(verdict) is CheckProvenance.SOURCE_BINDING


def test_scent_truthfulness_is_our_own_enrichment() -> None:
    """JDEC-018 needs a disclosed trajectory a lawful KIT peer never promised."""
    assert provenance_of(SemanticVerdict.DISHONEST_SCENT_EMISSION) is (
        CheckProvenance.PROJECT_ENRICHMENT
    )


def test_the_clean_verdict_carries_no_blocking_authority() -> None:
    assert provenance_of(SemanticVerdict.CONSISTENT) is CheckProvenance.PROJECT_ENRICHMENT


def test_the_matrix_is_immutable() -> None:
    import pytest

    with pytest.raises(TypeError):
        PROVENANCE[SemanticVerdict.CONSISTENT] = CheckProvenance.SOURCE_BINDING  # type: ignore[index]
