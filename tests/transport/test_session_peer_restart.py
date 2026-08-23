"""The rerun-8 interop failure, reproduced against a real server and survived.

Our outbound session is opened at startup, because opening it is what proves the
opponent is listening. In the rehearsal the opponent then restarted its own
runner before sub-game 1. The id we held named nothing, its server answered our
g01 greeting with HTTP 404, and the backend died on `E-TRANSPORT` having never
delivered a greeting - no sub-game played, the whole run lost.

Nothing here is simulated: a real FastMCP server is stopped and a new one is
started on the same port, which is what the peer's restart looked like from our
side. The assertion is that the greeting still arrives, on a session the peer
issued after its restart.
"""

import asyncio
import threading

import uvicorn
from peer_ops import commitment, step0_exchange
from peer_process import free_port
from peer_recorder import RecordingOperations

from mars777_police.app.peer_supervision import PeerDeadline, TimeoutPolicy
from mars777_police.transport.client import PeerClient
from mars777_police.transport.codec_declaration import encode_step0
from mars777_police.transport.codec_turn import encode_commitment
from mars777_police.transport.server import build_server
from mars777_police.transport.wire_errors import TransportFailureError

SETTLE_ATTEMPTS = 400
SETTLE_PAUSE = 0.05


def serve(port: int) -> tuple[RecordingOperations, uvicorn.Server]:
    """Start one real FastMCP server on *port* and hand back its control."""
    operations = RecordingOperations()
    server = uvicorn.Server(
        uvicorn.Config(
            build_server(operations).http_app(path="/mcp"),
            host="127.0.0.1",
            port=port,
            log_level="error",
        )
    )
    threading.Thread(target=server.run, daemon=True).start()
    return operations, server


async def settle(url: str) -> None:
    """Wait for a server on *url* by opening a real session, never by sleeping."""
    for _ in range(SETTLE_ATTEMPTS):
        try:
            async with PeerClient(url, PeerDeadline(TimeoutPolicy(5.0))):
                return
        except TransportFailureError:
            await asyncio.sleep(SETTLE_PAUSE)
    raise AssertionError("the local server never became reachable")


async def restart(server: uvicorn.Server, port: int, url: str) -> RecordingOperations:
    """Stop the peer and bring a fresh one up on the same address."""
    server.should_exit = True
    for _ in range(SETTLE_ATTEMPTS):
        if server.started is False:
            break
        await asyncio.sleep(SETTLE_PAUSE)
        if not server.started:
            break
    await asyncio.sleep(SETTLE_PAUSE)
    operations, _ = serve(port)
    await settle(url)
    return operations


def test_a_peer_that_restarts_before_the_first_sub_game_is_survived() -> None:
    """Step-0 lands on the first server, the greeting on the one that replaced it."""
    port = free_port()
    url = f"http://127.0.0.1:{port}/mcp"
    before, server = serve(port)

    async def drive() -> tuple[list[str], list[str], str | None, str | None, int]:
        await settle(url)
        client = PeerClient(url, PeerDeadline(TimeoutPolicy(20.0)))
        async with client:
            await client.complete("negotiate", "step0", encode_step0(step0_exchange()))
            first = client.session_id
            after = await restart(server, port, url)
            await client.complete("receive_turn", "commitment", encode_commitment(commitment()))
            second = client.session_id
            return before.kinds(), after.kinds(), first, second, client._hold.reestablished

    old, new, first, second, reestablished = asyncio.run(drive())
    assert "step0" in old
    assert "commitment" in new
    assert reestablished == 1
    assert first is not None and second is not None and first != second


def test_the_retired_identifier_is_never_sent_again() -> None:
    """A new session means a new `initialize`; the disowned id is not reused."""
    port = free_port()
    url = f"http://127.0.0.1:{port}/mcp"
    _, server = serve(port)

    async def drive() -> set[str | None]:
        await settle(url)
        client = PeerClient(url, PeerDeadline(TimeoutPolicy(20.0)))
        seen: set[str | None] = set()
        async with client:
            await client.complete("negotiate", "step0", encode_step0(step0_exchange()))
            seen.add(client.session_id)
            await restart(server, port, url)
            await client.complete("receive_turn", "commitment", encode_commitment(commitment()))
            seen.add(client.session_id)
        return seen

    assert len(asyncio.run(drive())) == 2
