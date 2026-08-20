"""Every refusal the reporting path can produce, exercised rather than assumed.

A refusal nobody has ever run is a refusal nobody knows the wording of, and
these are the paths an operator meets on a bad day: a malformed credential
file, a gate that has latched shut, a value that cannot be a report.
"""

import json
from pathlib import Path

import pytest
import report_fixtures as fix

from mars777_police.app.gatekeeper import Gatekeeper
from mars777_police.app.gatekeeper_admission import admission_for
from mars777_police.app.gatekeeper_bucket import TokenBucket
from mars777_police.app.gatekeeper_dos import DosDetector, ProviderLockedError
from mars777_police.app.gatekeeper_quota import DailyQuota
from mars777_police.app.report_service import SEND_REPORT
from mars777_police.app.report_values import GameReport, ReportDelivery, ReportError
from mars777_police.infra.gmail_credentials import GmailCredentialError, load_credentials
from mars777_police.infra.rate_limit_file import load_rate_limits
from mars777_police.shared.rate_limits import RateLimitConfigError, RateLimitPolicy


def policy(**overrides: object) -> RateLimitPolicy:
    fields: dict[str, object] = {
        "requests_per_minute": 30,
        "requests_per_hour": 50,
        "concurrent_max": 2,
        "queue_depth": 100,
        "max_retries": 3,
        "retry_after_seconds": 5,
        "max_backoff_seconds": 60,
        "retryable_statuses": (429,),
    }
    fields.update(overrides)
    return RateLimitPolicy(**fields)  # type: ignore[arg-type]


def test_an_unknown_admission_name_is_refused() -> None:
    with pytest.raises(RateLimitConfigError, match="admission must be one of"):
        policy(admission="magic")


def test_a_token_bucket_without_its_own_numbers_is_refused() -> None:
    with pytest.raises(RateLimitConfigError, match="burst_capacity"):
        policy(admission="token_bucket", daily_quota=50)


def test_half_a_dos_detector_is_refused() -> None:
    with pytest.raises(RateLimitConfigError, match="dos_burst_limit and dos_window_seconds"):
        policy(dos_burst_limit=10)


def test_a_token_bucket_may_be_configured_without_a_detector() -> None:
    clock = fix.Clock()
    chain = admission_for(
        policy(admission="token_bucket", burst_capacity=5, daily_quota=50), clock.monotonic
    )

    assert [type(one) for one in chain.mechanisms] == [DailyQuota, TokenBucket]


def test_a_latched_gate_refuses_the_call_and_records_the_refusal() -> None:
    clock = fix.Clock()
    keeper = Gatekeeper(load_rate_limits(), monotonic=clock.monotonic, sleeper=clock.sleep)
    limit = load_rate_limits().policy_for(SEND_REPORT).dos_burst_limit

    for _ in range(limit + 1):
        keeper.call(SEND_REPORT, lambda: "ok")

    with pytest.raises(ProviderLockedError, match="locked"):
        keeper.call(SEND_REPORT, lambda: "ok")
    assert keeper.calls[-1].outcome.value == "REFUSED"


def test_a_quota_or_detector_that_permits_nothing_is_refused_at_construction() -> None:
    clock = fix.Clock()

    with pytest.raises(ValueError, match="at least one call"):
        DailyQuota(0, clock.monotonic)
    with pytest.raises(ValueError, match="at least one call"):
        DosDetector(0, 60.0, clock.monotonic)
    with pytest.raises(ValueError, match="positive number of seconds"):
        DosDetector(3, 0.0, clock.monotonic)


def test_a_bucket_may_be_restored_at_an_explicit_level() -> None:
    clock = fix.Clock()
    held = TokenBucket(5.0, 0.5, clock.monotonic, tokens=2.0, last=clock.now)

    assert held.level == 2.0


@pytest.mark.parametrize("field", ["game_id", "group_id", "role", "result_sha256"])
def test_a_report_missing_a_required_identifier_is_refused(field: str) -> None:
    with pytest.raises(ReportError, match=field):
        fix.report(**{field: ""})


def test_a_report_without_the_document_it_attaches_is_refused() -> None:
    with pytest.raises(ReportError, match="result document"):
        fix.report(attachment=b"")


def test_an_accepted_delivery_is_the_one_that_counts_as_complete() -> None:
    assert ReportDelivery("id", True).complete is True
    assert ReportDelivery("id", False, failure="boom").complete is False


def test_a_report_error_raised_by_the_message_is_not_swallowed_as_a_delivery() -> None:
    service, _, _ = fix.service(fix.FakeGmail())
    hostile = GameReport("g\r\nBcc: x", "mars777", "police", fix.DIGEST, "r.json", b"{}")

    with pytest.raises(ReportError, match="control character"):
        service.send(hostile)


def test_an_unreadable_credential_file_is_refused_by_path(tmp_path: Path) -> None:
    with pytest.raises(GmailCredentialError, match="cannot read"):
        load_credentials(tmp_path / "absent.json")


def test_a_credential_file_that_is_not_json_is_refused(tmp_path: Path) -> None:
    target = tmp_path / "token.json"
    target.write_text("not json", encoding="utf-8")

    with pytest.raises(GmailCredentialError, match="not valid JSON"):
        load_credentials(target)


def test_a_credential_file_that_is_not_an_object_is_refused(tmp_path: Path) -> None:
    target = tmp_path / "token.json"
    target.write_text(json.dumps([1, 2, 3]), encoding="utf-8")

    with pytest.raises(GmailCredentialError, match="not a credential object"):
        load_credentials(target)


def test_a_credential_file_may_name_its_own_token_endpoint(tmp_path: Path) -> None:
    target = tmp_path / "token.json"
    target.write_text(
        json.dumps(
            {
                "client_id": "a",
                "client_secret": "b",
                "refresh_token": "c",
                "token_uri": "https://oauth2.example.test/token",
            }
        ),
        encoding="utf-8",
    )

    assert load_credentials(target).token_uri == "https://oauth2.example.test/token"
