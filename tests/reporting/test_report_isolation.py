"""What reporting must never touch: the official artifacts, and the game itself.

Appendix F Table 20 fixes the official set at one declaration, six configs, six
logs and one result. Delivery status is a fact about our outbox, so it must not
become a fifteenth graded file, and a provider failure must not be able to move
a single value the game decided.
"""

import json
from pathlib import Path

import report_fixtures as fix

from mars777_police.app.gatekeeper_retry import ProviderStatusError
from mars777_police.app.report_service import SEND_REPORT
from mars777_police.infra.report_evidence import EVIDENCE_DIRECTORY, evidence_name

OFFICIAL_PREFIXES = ("declaration_", "config_", "log_", "result_")


def test_the_delivery_record_carries_no_official_artifact_name() -> None:
    name = evidence_name(fix.GAME_ID)

    assert not any(name.startswith(prefix) for prefix in OFFICIAL_PREFIXES)
    assert name.startswith("delivery_")


def test_reporting_writes_outside_the_official_artifact_namespace(tmp_path: Path) -> None:
    from mars777_police.infra.report_evidence import write_evidence

    written = write_evidence(tmp_path, fix.GAME_ID, {"game_id": fix.GAME_ID})

    assert written.parent.name == EVIDENCE_DIRECTORY
    assert written.parent != tmp_path


def test_an_official_directory_still_holds_exactly_fourteen_files(tmp_path: Path) -> None:
    """The exact-six set is unchanged by a report having been delivered."""
    from mars777_police.infra.report_evidence import evidence_document, write_evidence

    official = tmp_path / "artifacts"
    official.mkdir()
    names = [
        f"declaration_{fix.GAME_ID}.json",
        *[f"config_{fix.GAME_ID}_g{one:02d}.json" for one in range(1, 7)],
        *[f"log_{fix.GAME_ID}_g{one:02d}.json" for one in range(1, 7)],
        f"result_{fix.GAME_ID}.json",
    ]
    for name in names:
        (official / name).write_text("{}", encoding="utf-8")
    assert len(list(official.iterdir())) == 14

    delivery = fix.report()
    from mars777_police.app.report_values import ReportDelivery

    write_evidence(
        official,
        fix.GAME_ID,
        evidence_document(
            ReportDelivery(delivery.identity, True, "17f0"), fix.GAME_ID, SEND_REPORT
        ),
    )

    files = [one for one in official.iterdir() if one.is_file()]
    assert len(files) == 14


def test_the_delivery_record_holds_no_credential(tmp_path: Path) -> None:
    from mars777_police.app.report_values import ReportDelivery
    from mars777_police.infra.report_evidence import evidence_document

    document = evidence_document(
        ReportDelivery("id", False, failure="GmailSendError: 500"), fix.GAME_ID, SEND_REPORT
    )

    rendered = json.dumps(document).lower()
    for secret in ("bearer", "authorization", "refresh_token", "client_secret", "access_token"):
        assert secret not in rendered


def test_a_provider_failure_leaves_the_result_document_byte_identical(tmp_path: Path) -> None:
    result = fix.written_result(tmp_path)
    before = result.read_bytes()
    provider = fix.FakeGmail([ProviderStatusError(500)] * 8)
    service, _, _ = fix.service(provider)

    delivery = service.send(fix.report(attachment=before))

    assert delivery.accepted is False
    assert result.read_bytes() == before


def test_an_accepted_report_is_not_sent_a_second_time_by_this_process() -> None:
    provider = fix.FakeGmail(["msg-1", "msg-2"])
    service, _, _ = fix.service(provider)
    report = fix.report()

    first = service.send(report)
    second = service.send(report)

    assert len(provider.sent) == 1
    assert second is first
    assert service.status_of(report) is first


def test_a_failed_report_may_be_attempted_again_because_nothing_was_delivered() -> None:
    provider = fix.FakeGmail([ProviderStatusError(403), "msg-1"])
    service, _, _ = fix.service(provider)
    report = fix.report()

    assert service.send(report).accepted is False
    assert service.send(report).accepted is True
