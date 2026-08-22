"""A restart must not mail the lecturer a second time.

Appendix E rule 35 penalises a *contradictory* report with 0 for both groups, so
sending the same series twice is not a harmless duplicate. `ReportService`
already refuses a second send inside one process; this is the part that survives
the process dying - the delivery record was always written, but nothing read it
back.

The key is the report identity - the agreed result digest - not the file name.
A different agreed result under the same `game_id` is a different report and
must never inherit an earlier receipt.
"""

from pathlib import Path

import pytest

from mars777_police.app.report_values import ReportDelivery
from mars777_police.infra.report_evidence import (
    EVIDENCE_DIRECTORY,
    accepted_identity,
    evidence_document,
    evidence_name,
    write_evidence,
)


def _write(root: Path, game_id: str, identity: str, accepted: bool) -> Path:
    delivery = ReportDelivery(identity, accepted, provider_message_id="m1" if accepted else None)
    return write_evidence(root, game_id, evidence_document(delivery, game_id, "gmail.send_report"))


def test_no_record_means_nothing_was_delivered(tmp_path: Path) -> None:
    assert accepted_identity(tmp_path, "g1") is None


def test_an_accepted_record_reports_the_identity_it_delivered(tmp_path: Path) -> None:
    _write(tmp_path, "g1", "digest-aaa", accepted=True)

    assert accepted_identity(tmp_path, "g1") == "digest-aaa"


def test_a_failed_record_is_not_a_delivery(tmp_path: Path) -> None:
    """A previous failure must not block a retry - that would lose the report."""
    _write(tmp_path, "g1", "digest-aaa", accepted=False)

    assert accepted_identity(tmp_path, "g1") is None


def test_a_different_agreed_result_never_inherits_an_earlier_receipt(tmp_path: Path) -> None:
    """Same game_id, different digest: a different report, and it must be sent."""
    _write(tmp_path, "g1", "digest-aaa", accepted=True)

    assert accepted_identity(tmp_path, "g1") != "digest-bbb"


def test_the_record_carries_no_secret(tmp_path: Path) -> None:
    written = _write(tmp_path, "g1", "digest-aaa", accepted=True)
    body = written.read_text(encoding="utf-8").lower()

    for secret in ("token", "secret", "bearer", "refresh", "client_id", "password"):
        assert secret not in body


def test_a_corrupt_record_is_treated_as_no_delivery(tmp_path: Path) -> None:
    """An unreadable receipt must not silently suppress a required report."""
    directory = tmp_path / EVIDENCE_DIRECTORY
    directory.mkdir(parents=True, exist_ok=True)
    (directory / evidence_name("g1")).write_text("{not json", encoding="utf-8")

    assert accepted_identity(tmp_path, "g1") is None


def test_the_record_lives_outside_the_official_artifact_namespace(tmp_path: Path) -> None:
    written = _write(tmp_path, "g1", "digest-aaa", accepted=True)

    assert written.name.startswith("delivery_")
    assert written.parent.name == EVIDENCE_DIRECTORY == "reporting"
    for official in ("result_", "log_", "config_", "declaration_"):
        assert not written.name.startswith(official)


def test_a_second_send_of_an_already_delivered_result_never_reaches_the_provider(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The restart case, proved through the real entry point.

    `send_game_report` is asked twice for the same agreed result. The second
    call must return the recorded delivery without constructing a sender - a
    restarted agent mailing the lecturer again is exactly what Appendix E rule
    35 penalises.
    """
    from mars777_police import compose_report

    result = tmp_path / "result_g1.json"
    result.write_text('{"game_id": "g1"}', encoding="utf-8")

    class Report:
        game_id = "g1"
        identity = "digest-aaa"

    monkeypatch.setattr(compose_report, "read_report", lambda one, two: Report())
    monkeypatch.setattr(
        compose_report,
        "GmailSender",
        lambda *args: pytest.fail("a delivered report must not reach the provider again"),
    )
    _write(tmp_path, "g1", "digest-aaa", accepted=True)

    outcome = compose_report.send_game_report(result)

    assert outcome.delivery.accepted is True
    assert outcome.delivery.identity == "digest-aaa"
