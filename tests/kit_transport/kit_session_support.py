"""Building a KIT-mode peer, in memory and over real HTTP.

The server, the registration, the codecs and the router are production. What a
test supplies is the *context* every KIT process is composed with - our group,
our role, our terms and which sub-game is running - because a kit turn numbers
only its own chain and says nothing about the sub-game it belongs to.
"""

import threading
import time

import uvicorn
from peer_process import free_port

from mars777_police.app.kit_messages import KitRole
from mars777_police.app.kit_payload import PeerPayload
from mars777_police.app.kit_session import KitSessionContext
from mars777_police.transport.handlers import PeerOperations
from mars777_police.transport.server import build_server
from mars777_police.transport.transport_profiles import TransportEnvelopeProfile

READY_TIMEOUT = 15.0
TERMS = {"grid_size": 10, "max_steps": 35}
OUR_GROUP = "MaRs-777"


def kit_context(sub_game: int = 1, role: KitRole = KitRole.THIEF) -> KitSessionContext:
    """One process's out-of-band context: who we are and what we agreed to."""
    return KitSessionContext(OUR_GROUP, role, PeerPayload(TERMS), sub_game)


def kit_server(operations: PeerOperations, context: KitSessionContext) -> object:
    """A KIT-profile peer server, chosen before construction and never after."""
    return build_server(
        operations,
        name="mars777-kit-peer",
        profile=TransportEnvelopeProfile.KIT_EXTERNAL,
        context=context,
    )


class KitLiveServer:
    """One KIT-mode peer server, served over real HTTP in a background thread."""

    def __init__(self, operations: PeerOperations, context: KitSessionContext) -> None:
        self.port = free_port()
        application = kit_server(operations, context).http_app(path="/mcp")  # type: ignore[attr-defined]
        config = uvicorn.Config(application, host="127.0.0.1", port=self.port, log_level="error")
        self._server = uvicorn.Server(config)
        self._thread = threading.Thread(target=self._server.run, daemon=True)

    @property
    def url(self) -> str:
        """The ingress a KIT peer would be given."""
        return f"http://127.0.0.1:{self.port}/mcp"

    def __enter__(self) -> "KitLiveServer":
        self._thread.start()
        deadline = time.monotonic() + READY_TIMEOUT
        while not self._server.started and time.monotonic() < deadline:
            time.sleep(0.05)
        if not self._server.started:
            raise RuntimeError("the KIT peer server never became ready")
        return self

    def __exit__(self, kind: object, value: object, traceback: object) -> None:
        self._server.should_exit = True
        self._thread.join(timeout=10)
