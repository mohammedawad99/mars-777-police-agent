"""The provider surface that exists today, and the one that will exist later.

Two things are proved here: tunnel discovery really is counted and bounded by
the gate, with its behaviour unchanged; and a future reporting surface can
register with the same gate without the gate learning anything about reporting.
"""

from pathlib import Path

import pytest

from mars777_police.app.gatekeeper import Gatekeeper
from mars777_police.app.gatekeeper_events import CallOutcome
from mars777_police.app.gatekeeper_retry import ProviderStatusError
from mars777_police.compose_gateway import DISCOVER_TUNNELS, gated_fetcher
from mars777_police.infra.rate_limit_file import load_rate_limits
from mars777_police.shared.rate_limits import RateLimitConfig, RateLimitPolicy


def test_the_shipped_policy_lets_discovery_poll_at_its_own_cadence() -> None:
    """Discovery polls twice a second for its whole window; the ceiling is above that."""
    policy = load_rate_limits().policy_for(DISCOVER_TUNNELS)

    assert policy.requests_per_minute > 120
    assert policy.max_retries == 0


def test_discovery_is_counted_by_the_gate(monkeypatch: pytest.MonkeyPatch) -> None:
    keeper = Gatekeeper(load_rate_limits())
    monkeypatch.setattr("mars777_police.compose_gateway.fetch", lambda url: b"{}")

    assert gated_fetcher(keeper)("http://127.0.0.1:1/api/tunnels") == b"{}"
    assert keeper.calls[-1].operation == DISCOVER_TUNNELS
    assert keeper.calls[-1].outcome is CallOutcome.SUCCEEDED


def test_a_transport_failure_still_reaches_the_discovery_loop_as_an_oserror(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The loop treats `OSError` as "not registered yet"; that must not change."""
    keeper = Gatekeeper(load_rate_limits())

    def refuse(url: str) -> bytes:
        raise OSError("connection refused")

    monkeypatch.setattr("mars777_police.compose_gateway.fetch", refuse)

    with pytest.raises(OSError, match="connection refused"):
        gated_fetcher(keeper)("http://127.0.0.1:1/api/tunnels")


def test_the_composed_launcher_reads_the_provider_through_the_gate(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from executable_process import environment

    from mars777_police.compose_gateway import compose_public_gateway
    from mars777_police.operator_requests import PublicGatewayRequest

    for name, value in environment(root=tmp_path).items():
        monkeypatch.setenv(name, value)
    launcher = compose_public_gateway(
        PublicGatewayRequest(
            police_endpoint="http://127.0.0.1:1/mcp",
            thief_endpoint="http://127.0.0.1:2/mcp",
            ngrok=Path("/usr/bin/ngrok"),
        )
    )

    fetcher = launcher.network.ingress.fetcher  # type: ignore[union-attr]
    assert fetcher.__qualname__.startswith("gated_fetcher")


def test_a_future_reporting_surface_reuses_the_same_gate_unchanged() -> None:
    """No new limiter, no gate change - a registered policy and a callable.

    This is a fake provider standing in for the Gmail sender that does not exist
    yet. What it proves is the seam: the reporting slice will bring its own
    policy entry and its own callable, and the gate will not learn what a report
    is.
    """
    sending = RateLimitPolicy(
        requests_per_minute=6,
        requests_per_hour=60,
        concurrent_max=1,
        queue_depth=4,
        max_retries=2,
        retry_after_seconds=5,
        max_backoff_seconds=30,
        retryable_statuses=(429,),
    )
    slept: list[float] = []
    keeper = Gatekeeper(
        RateLimitConfig("1.00", load_rate_limits().default, {"reporting.send_report": sending}),
        sleeper=slept.append,
    )
    answers = [ProviderStatusError(429, retry_after=9.0), None]

    def send() -> str:
        outcome = answers.pop(0)
        if outcome is not None:
            raise outcome
        return "sent"

    assert keeper.call("reporting.send_report", send) == "sent"
    assert slept == [9.0]
    assert keeper.calls[-1].attempts == 2
