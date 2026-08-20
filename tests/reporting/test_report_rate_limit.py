"""What the Gmail send path does when the provider pushes back.

Ch 9's iron rule: *"exceeding Google's API quota is returned as HTTP 429 (Too
Many Requests). This error is not a passing fault - blind insistence and
immediate resending after it may lead to suspension of the account by the
provider. One must respect the 429, back off, and wait for the next window."*

Every wait here is recorded on an injected sleeper. Nothing sleeps.
"""

import pytest
import report_fixtures as fix

from mars777_police.app.gatekeeper_retry import ProviderStatusError
from mars777_police.app.report_service import SEND_REPORT
from mars777_police.infra.rate_limit_file import load_rate_limits

POLICY = load_rate_limits().policy_for(SEND_REPORT)


def test_a_429_is_never_retried_immediately() -> None:
    provider = fix.FakeGmail([ProviderStatusError(429), "msg-1"])
    service, _, clock = fix.service(provider)

    delivery = service.send(fix.report())

    assert delivery.accepted is True
    assert clock.slept and min(clock.slept) >= float(POLICY.retry_after_seconds)


def test_the_provider_s_own_retry_after_is_honoured_when_it_sends_one() -> None:
    provider = fix.FakeGmail([ProviderStatusError(429, retry_after=17.0), "msg-1"])
    service, _, clock = fix.service(provider)

    service.send(fix.report())

    assert 17.0 in clock.slept


def test_an_absurd_retry_after_is_clamped_by_our_own_configured_maximum() -> None:
    provider = fix.FakeGmail([ProviderStatusError(429, retry_after=86_400.0), "msg-1"])
    service, _, clock = fix.service(provider)

    service.send(fix.report())

    assert max(clock.slept) <= float(POLICY.max_backoff_seconds)


def test_repeated_429s_back_off_further_each_time_and_then_stop() -> None:
    refusals = [ProviderStatusError(429) for _ in range(POLICY.max_retries + 1)]
    provider = fix.FakeGmail(list(refusals))
    service, _, _ = fix.service(provider)

    delivery = service.send(fix.report())

    assert delivery.accepted is False
    assert len(provider.sent) == POLICY.max_retries + 1
    assert "429" in str(delivery.failure)


@pytest.mark.parametrize("status", [500, 502, 503, 504])
def test_a_server_side_failure_is_retried_because_the_policy_names_it(status: int) -> None:
    provider = fix.FakeGmail([ProviderStatusError(status), "msg-1"])
    service, _, _ = fix.service(provider)

    assert service.send(fix.report()).accepted is True


@pytest.mark.parametrize("status", [400, 401, 403, 404])
def test_a_client_side_failure_is_never_repeated(status: int) -> None:
    provider = fix.FakeGmail([ProviderStatusError(status), "msg-1"])
    service, _, _ = fix.service(provider)

    delivery = service.send(fix.report())

    assert delivery.accepted is False
    assert len(provider.sent) == 1


def test_a_transport_failure_is_retried_and_then_reported_as_a_failure() -> None:
    provider = fix.FakeGmail([OSError("connection reset"), OSError("connection reset"), "msg-1"])
    service, _, _ = fix.service(provider)

    assert service.send(fix.report()).accepted is True


def test_the_bucket_delays_a_burst_rather_than_letting_it_reach_the_provider() -> None:
    provider = fix.FakeGmail([f"msg-{one}" for one in range(POLICY.burst_capacity + 2)])
    service, _, clock = fix.service(provider)

    for index in range(POLICY.burst_capacity + 2):
        service.send(fix.report(result_sha256=f"{index:064d}"))

    assert clock.slept, "a burst past the capacity must have waited for a refill"
    assert len(provider.sent) == POLICY.burst_capacity + 2
