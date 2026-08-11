"""The ngrok adapter that satisfies `PublicIngressPort`.

This is the **only** module in the project that is both provider-specific and
reachable from a running peer, and it is intentionally thin: the process lives
in `ngrok_process`, the wire shape in `agent_api`, and the endpoint semantics in
`app`. What remains here is the sequence - start, poll, join the origin to the
FastMCP path, hand back a semantic value.

Conformance to the port is **structural**. This class never imports
`PublicIngressPort`, so the application cannot acquire a dependency on ngrok by
importing the thing that implements its port.

The bounded poll is not defensiveness. The installed agent answers its API with
an empty collection while registration is still in flight, so a single read
would intermittently report no endpoint at all.
"""

import time
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass, field

from ..app.public_endpoint_values import LocalPeerEndpoint, OwnPublicPeerEndpoint, public_url_for
from ..app.public_ingress import PublicIngressError
from .agent_api import TUNNELS_RESOURCE, parse_tunnels, select_for
from .ngrok_process import NgrokProcess


def fetch(url: str) -> bytes:
    """Read a loopback Agent API resource using the standard library only."""
    request = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=8.0) as response:
        body: bytes = response.read()
    return body


@dataclass(slots=True)
class NgrokPublicIngress:
    """One group-level public route, provided by the external ngrok Agent."""

    agent: NgrokProcess
    fetcher: Callable[[str], bytes] = fetch
    monotonic: Callable[[], float] = time.monotonic
    sleeper: Callable[[float], None] = time.sleep
    endpoint: OwnPublicPeerEndpoint | None = field(default=None)

    def open(self, local: LocalPeerEndpoint) -> OwnPublicPeerEndpoint:
        """Expose *local* and return the public MCP endpoint now serving it."""
        api_base = self.agent.start(local.port)
        try:
            entry = self._discover(api_base, local.port)
        except PublicIngressError:
            self.agent.stop()
            raise
        self.endpoint = public_url_for(entry)
        return self.endpoint

    def _discover(self, api_base: str, port: int) -> str:
        settings = self.agent.settings
        deadline = self.monotonic() + settings.discovery_seconds
        while True:
            try:
                entries = parse_tunnels(self.fetcher(api_base + TUNNELS_RESOURCE))
            except OSError:
                entries = ()
            chosen = select_for(entries, port)
            if chosen is not None:
                return chosen.public_url
            if self.monotonic() >= deadline:
                raise PublicIngressError("no public endpoint appeared before the deadline")
            self.sleeper(settings.poll_seconds)

    def current(self) -> OwnPublicPeerEndpoint | None:
        """The endpoint presently served, or `None` when closed."""
        return self.endpoint if self.agent.is_running else None

    def is_live(self) -> bool:
        """Whether the route is established right now."""
        return self.agent.is_running and self.endpoint is not None

    def close(self) -> None:
        """Tear the route down; idempotent, and always safe after a failure."""
        self.agent.stop()
        self.endpoint = None
