"""Persisting evidence changes nothing about what a friendly is worth.

Writing files is the one operation that most looks like it might promote a run,
so each promotion it must **not** cause is pinned separately: counted readiness,
counted mail, league diversity, and the counted writers themselves.
"""

import pytest
from r16_builders import GAME_ID
from test_friendly_evidence import evidence
from test_friendly_evidence_store import _Store
from test_readiness_gate import facts

from mars777_police.app.friendly_evidence import (
    DevelopmentEvidenceStore,
    persist_friendly_evidence,
)
from mars777_police.app.protocol_errors import LocalDefectError
from mars777_police.app.public_readiness_gate import ReadinessCheck, evaluate
from mars777_police.app.run_class import RunClassification


def persisted() -> tuple[_Store, object]:
    inner = _Store()
    held = evidence()
    persist_friendly_evidence(DevelopmentEvidenceStore(inner), held)
    return inner, held


def test_a_fully_persisted_friendly_still_refuses_counted_readiness() -> None:
    _, held = persisted()

    verdict = evaluate(facts(step0_authenticated=held.classification.step0_authenticated))

    assert verdict.is_ready is False
    assert ReadinessCheck.STEP0_AUTHENTICATED in {one.check for one in verdict.failures}


def test_persisting_evidence_does_not_make_the_run_counted() -> None:
    _, held = persisted()

    assert held.classification.counted_capable is False


def test_persisted_development_evidence_cannot_enter_the_counted_mail_path() -> None:
    """A reporting owner exists since Stage 9A-2C, and this is what keeps it shut.

    The guard used to assert that no mailer existed at all, which stopped being
    the property once one had to exist. What actually protects a friendly is
    that the report reader demands the mutual agreement a development document
    states it does **not** have - so this proves the refusal instead.
    """
    from mars777_police.app.friendly_evidence import series_document
    from mars777_police.app.report_source import reportable_facts
    from mars777_police.app.report_values import ReportIneligibleError

    _inner, held = persisted()
    document = series_document(held)

    assert document["evidence_class"]
    assert "mutual_agreement" not in document
    with pytest.raises(ReportIneligibleError, match="mutual agreement"):
        reportable_facts(document, "friendly evidence")


def test_persisted_evidence_claims_no_diversity_or_league_credit() -> None:
    inner, _ = persisted()
    rendered = repr(inner.written)

    for forbidden in ("diversity", "counted_games", "league", "first_meeting", "winner_group"):
        assert forbidden not in rendered


def test_every_persisted_document_names_itself_development_evidence() -> None:
    inner, _ = persisted()

    assert all(one["evidence_class"] == "DEVELOPMENT_EVIDENCE" for one in inner.written.values())


def test_the_counted_writers_still_refuse_what_a_friendly_cannot_supply() -> None:
    """The three preconditions a KIT friendly never satisfies, still enforced."""
    from mars777_police.app.pregame_session_runtime import PregameSessionRuntime
    from mars777_police.artifact_documents import config_document, result_document

    unlocked = object.__new__(PregameSessionRuntime)
    object.__setattr__(unlocked, "locked_evidence", None)

    with pytest.raises(LocalDefectError):
        config_document(object(), unlocked)  # type: ignore[arg-type]

    empty = object.__new__(_ResultExchangeStub)
    with pytest.raises(LocalDefectError):
        result_document(empty, "MaRs-777")  # type: ignore[arg-type]


class _ResultExchangeStub:
    """A result exchange that never agreed anything - the friendly's situation."""

    local_digest = None


def test_the_official_result_document_is_the_only_place_agreement_is_claimed() -> None:
    """`mutual_agreement` belongs to a file a friendly cannot produce.

    Naming it is not claiming it: the reporting reader added at Stage 9A-2C
    *demands* the field before it will report, which is the opposite of writing
    one. So the guard is on the write, which is where the claim is made.
    """
    from pathlib import Path

    src = Path(__file__).resolve().parents[2] / "src"
    claimants = [
        path.name
        for path in src.rglob("*.py")
        if '["mutual_agreement"] =' in path.read_text(encoding="utf-8")
    ]

    assert claimants == ["artifact_documents.py"]


def test_a_development_name_can_never_be_written_by_the_counted_owner() -> None:
    """And the converse: the development store refuses every counted name."""
    from mars777_police.app.artifact_store import declaration_name

    store = DevelopmentEvidenceStore(_Store())

    with pytest.raises(LocalDefectError):
        store.store(declaration_name(GAME_ID), {})


def test_a_counted_classification_persisted_here_would_still_be_development() -> None:
    """The store is named by what it writes, not by what a caller believes."""
    inner = _Store()
    held = evidence()
    object.__setattr__(held, "classification", RunClassification.counted(keyed_auth_satisfied=True))

    persist_friendly_evidence(DevelopmentEvidenceStore(inner), held)

    assert all(str(name).startswith("friendly_") for name in inner.written)
