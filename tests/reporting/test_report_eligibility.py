"""When a result may become an email, and every way it may not.

Appendix E rule 35 makes the mutual agreement the condition for being credited
at all: *"non-reporting by one of the groups, or a contradictory report, causes
disqualification of the game and a grade of 0 for both groups."* So a report
that is not yet eligible must be refused rather than sent, and none of these
refusals may be reachable by an operator in a hurry.
"""

import pytest
import report_fixtures as fix

from mars777_police.app.protocol_values import Sha256Digest
from mars777_police.app.report_eligibility import REPORTABLE, report_for, require_reportable
from mars777_police.app.report_source import reportable_facts
from mars777_police.app.report_values import ReportIneligibleError
from mars777_police.app.state_machine import ProtocolPhase


def eligible(**overrides: object) -> object:
    fields: dict[str, object] = {
        "phase": ProtocolPhase.REPORT_READY,
        "agreed": True,
        "game_id": fix.GAME_ID,
        "group_id": "mars777",
        "role": "police",
        "result_sha256": Sha256Digest(fix.DIGEST),
        "attachment_name": "result.json",
        "attachment": b"{}",
    }
    fields.update(overrides)
    return report_for(**fields)  # type: ignore[arg-type]


def test_the_only_reportable_phase_is_the_terminal_reporting_one() -> None:
    assert REPORTABLE is ProtocolPhase.REPORT_READY
    require_reportable(ProtocolPhase.REPORT_READY)


@pytest.mark.parametrize(
    "phase",
    [ProtocolPhase.READY, ProtocolPhase.SERIES_COMPLETE, ProtocolPhase.FINAL_AUDIT],
)
def test_a_series_that_has_not_finished_cannot_be_reported(phase: ProtocolPhase) -> None:
    with pytest.raises(ReportIneligibleError, match="REPORT_READY"):
        require_reportable(phase)


def test_a_result_without_a_mutual_agreement_is_refused() -> None:
    with pytest.raises(ReportIneligibleError, match="mutual agreement"):
        eligible(agreed=False)


def test_an_agreed_result_without_its_digest_is_refused() -> None:
    with pytest.raises(ReportIneligibleError, match="digest"):
        eligible(result_sha256=None)


def test_an_eligible_result_becomes_a_report_that_names_its_own_identity() -> None:
    report = eligible()

    assert report.identity == f"{fix.GAME_ID}:{fix.DIGEST}"  # type: ignore[attr-defined]


def test_a_stored_document_must_record_the_agreement_it_claims() -> None:
    with pytest.raises(ReportIneligibleError, match="mutual agreement"):
        reportable_facts(fix.result_document(mutual_agreement=False), "result.json")


def test_a_stored_document_missing_a_required_field_is_refused() -> None:
    document = fix.result_document()
    del document["reported_by"]

    with pytest.raises(ReportIneligibleError, match="reported_by"):
        reportable_facts(document, "result.json")


def test_a_stored_document_with_an_unusable_digest_is_refused() -> None:
    with pytest.raises(ReportIneligibleError, match="digest is unusable"):
        reportable_facts(fix.result_document(result_sha256="not-a-digest"), "result.json")


def test_a_well_formed_agreed_document_yields_exactly_its_three_facts() -> None:
    game_id, group_id, digest = reportable_facts(fix.result_document(), "result.json")

    assert (game_id, group_id, digest.value) == (fix.GAME_ID, "mars777", fix.DIGEST)
