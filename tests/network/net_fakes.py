"""Deterministic stand-ins for everything R18 would otherwise need a network for.

None of these fake the *decision* under test. The resolver returns addresses, the
fetcher returns bytes, the spawned agent returns log lines - each is a source of
facts, never a source of verdicts, so a defect in the production policy still
fails the test that uses them.
"""

import json
from dataclasses import dataclass, field

from mars777_police.app.public_endpoint_values import LocalPeerEndpoint, OwnPublicPeerEndpoint

PUBLIC_HOST = "exposure-example.ngrok-free.dev"
PUBLIC_URL = f"https://{PUBLIC_HOST}/mcp"
OTHER_URL = "https://other-example.ngrok-free.dev/mcp"


@dataclass(slots=True)
class FakeResolver:
    """A `HostResolver` whose answers the test chooses."""

    answers: dict[str, tuple[str, ...]] = field(default_factory=dict)
    default: tuple[str, ...] = ("3.125.102.39",)

    def resolve(self, host: str) -> tuple[str, ...]:
        return self.answers.get(host, self.default)


@dataclass(slots=True)
class FakeIngress:
    """A `PublicIngressPort` with no provider behind it."""

    endpoint: OwnPublicPeerEndpoint = field(
        default_factory=lambda: OwnPublicPeerEndpoint(PUBLIC_URL)
    )
    live: bool = False
    opened: list[LocalPeerEndpoint] = field(default_factory=list)
    closed: int = 0

    def open(self, local: LocalPeerEndpoint) -> OwnPublicPeerEndpoint:
        self.opened.append(local)
        self.live = True
        return self.endpoint

    def current(self) -> OwnPublicPeerEndpoint | None:
        return self.endpoint if self.live else None

    def is_live(self) -> bool:
        return self.live

    def close(self) -> None:
        self.closed += 1
        self.live = False


def tunnels_body(entries: list[dict[str, object]]) -> bytes:
    """An `/api/tunnels` body in the exact measured 3.39.10 shape."""
    return json.dumps({"tunnels": entries, "uri": "/api/tunnels"}).encode()


def tunnel_entry(port: int, url: str = PUBLIC_URL.removesuffix("/mcp")) -> dict[str, object]:
    """One measured tunnel entry pointing at *port*."""
    return {
        "ID": f"id-{port}",
        "name": "command_line",
        "proto": "https",
        "public_url": url,
        "uri": f"/api/tunnels/{port}",
        "metrics": {},
        "config": {"addr": f"http://localhost:{port}", "inspect": True},
    }


@dataclass(slots=True)
class FakeClock:
    """A monotonic clock that only advances when the code under test sleeps."""

    now: float = 0.0

    def monotonic(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.now += seconds
