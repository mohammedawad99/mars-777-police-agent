"""The adapter: bounded polling over the measured empty-200 window, then a join.

The registration race is the reason this class exists in the shape it does. A
single read would intermittently find nothing, so the poll is asserted to
survive an empty collection, a transport error and a foreign entry before ours
appears.
"""

from pathlib import Path

import pytest
from fake_agent import FakeAgent
from net_fakes import PUBLIC_URL, FakeClock, tunnel_entry, tunnels_body

from mars777_police.app.public_endpoint_values import LocalPeerEndpoint
from mars777_police.app.public_ingress import PublicIngressError
from mars777_police.infra.ngrok_ingress import NgrokPublicIngress, fetch
from mars777_police.infra.ngrok_process import NgrokProcess
from mars777_police.infra.ngrok_settings import NgrokSettings

LOCAL = LocalPeerEndpoint("127.0.0.1", 8801)


def build(bodies: list[object], agent: FakeAgent | None = None) -> NgrokPublicIngress:
    agent = agent or FakeAgent()
    clock = FakeClock()
    runner = NgrokProcess(
        NgrokSettings(Path("/opt/ngrok"), discovery_seconds=5.0, poll_seconds=1.0),
        spawner=lambda argv: agent,
        monotonic=clock.monotonic,
    )
    queue = list(bodies)

    def fetcher(url: str) -> bytes:
        assert url.endswith("/api/tunnels")
        item = queue.pop(0) if queue else tunnels_body([])
        if isinstance(item, Exception):
            raise item
        assert isinstance(item, bytes)
        return item

    return NgrokPublicIngress(runner, fetcher, clock.monotonic, clock.sleep)


def test_the_endpoint_is_discovered_after_the_measured_empty_window() -> None:
    ingress = build(
        [
            tunnels_body([]),
            OSError("agent api not up yet"),
            tunnels_body([tunnel_entry(9999)]),
            tunnels_body([tunnel_entry(8801)]),
        ]
    )
    assert ingress.open(LOCAL).url == PUBLIC_URL
    assert ingress.is_live()
    assert ingress.current() is not None


def test_the_public_endpoint_preserves_the_exact_mcp_path() -> None:
    ingress = build([tunnels_body([tunnel_entry(8801)])])
    url = ingress.open(LOCAL).url
    assert url.endswith("/mcp")
    assert "//mcp" not in url
    assert "?" not in url and "#" not in url


def test_a_never_registering_endpoint_times_out_and_stops_the_agent() -> None:
    agent = FakeAgent()
    ingress = build([tunnels_body([])] * 20, agent)
    with pytest.raises(PublicIngressError, match="deadline"):
        ingress.open(LOCAL)
    assert agent.terminated == 1


def test_malformed_provider_json_stops_the_agent_and_fails_locally() -> None:
    agent = FakeAgent()
    ingress = build([b"not json"], agent)
    with pytest.raises(PublicIngressError):
        ingress.open(LOCAL)
    assert agent.terminated == 1


def test_closing_is_idempotent_and_forgets_the_endpoint() -> None:
    agent = FakeAgent()
    ingress = build([tunnels_body([tunnel_entry(8801)])], agent)
    ingress.open(LOCAL)
    ingress.close()
    ingress.close()
    assert ingress.current() is None
    assert not ingress.is_live()
    assert ingress.endpoint is None


def test_a_dead_agent_reports_no_current_endpoint() -> None:
    agent = FakeAgent()
    ingress = build([tunnels_body([tunnel_entry(8801)])], agent)
    ingress.open(LOCAL)
    agent.alive = False
    assert ingress.current() is None
    assert not ingress.is_live()


def test_the_real_fetcher_uses_only_the_standard_library() -> None:
    import inspect

    source = inspect.getsource(fetch)
    assert "urllib" in source
    for package in ("requests", "httpx", "aiohttp"):
        assert package not in source
