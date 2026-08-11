"""One live public ingress, shared by every live module in this directory.

Session-scoped deliberately, and not only for speed. `PRD05-FR-015` gives a
group **one stable ingress for the series**, so raising and tearing down an
agent between assertions would contradict the model under test. It also removes
a failure we measured: back-to-back start/stop cycles on this account
intermittently had the provider terminate a freshly established session
mid-request, because the previous one had not yet been released.

The peer behind it runs the **production** runtimes, so a refusal in any test
below comes from the application rather than from a fixture.

Nothing here runs when the live switch is off - the fixture is only built for a
test that asks for it, and every such test is skipped.
"""

import sys
from collections.abc import Iterator
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "transport"))

import pytest
from live_peer import LivePeerProcess
from live_support import ingress
from peer_process import free_port

from mars777_police.app.public_endpoint_values import LocalPeerEndpoint, OwnPublicPeerEndpoint
from mars777_police.infra.ngrok_ingress import NgrokPublicIngress

LivePeer = tuple[NgrokPublicIngress, OwnPublicPeerEndpoint, LivePeerProcess]


@pytest.fixture(scope="session")
def public_peer(tmp_path_factory: pytest.TempPathFactory) -> Iterator[LivePeer]:
    """One production peer process behind one real public ngrok endpoint."""
    status: Path = tmp_path_factory.mktemp("live") / "peer.json"
    port = free_port()
    route = ingress()
    with LivePeerProcess(port, status) as peer:
        try:
            yield route, route.open(LocalPeerEndpoint("127.0.0.1", port)), peer
        finally:
            route.close()
