"""The held-session lifecycle, driven against a real in-process FastMCP server.

The measurement that justified this lifecycle needed a public tunnel, but the
*behaviour* does not: whether one session serves many calls, whether it closes
exactly once, and whether a dead endpoint stays a transport failure are all
observable locally. That keeps the branch covered with no network, no provider
and no credential.
"""

import asyncio
import threading

import pytest
import uvicorn
from peer_ops import commitment, reveal, step0_exchange
from peer_process import free_port
from peer_recorder import RecordingOperations

from mars777_police.transport.client import PeerClient
from mars777_police.transport.codec_declaration import encode_step0
from mars777_police.transport.codec_turn import encode_commitment, encode_reveal
from mars777_police.transport.server import build_server
from mars777_police.transport.wire_errors import TransportFailureError

OPERATIONS = 12


def serve() -> tuple[RecordingOperations, str]:
    """Start one real FastMCP server in this process and return its URL."""
    operations = RecordingOperations()
    port = free_port()
    server = uvicorn.Server(
        uvicorn.Config(
            build_server(operations).http_app(path="/mcp"),
            host="127.0.0.1",
            port=port,
            log_level="error",
        )
    )
    threading.Thread(target=server.run, daemon=True).start()
    return operations, f"http://127.0.0.1:{port}/mcp"


async def settle(url: str) -> None:
    for _ in range(400):
        try:
            async with PeerClient(url, timeout=5.0):
                return
        except TransportFailureError:
            await asyncio.sleep(0.05)
    raise AssertionError("the local server never became reachable")


def test_one_held_session_serves_many_operations() -> None:
    """Twelve calls, one session - the property the public measurement demanded."""
    operations, url = serve()

    async def drive() -> list[object]:
        await settle(url)
        client = PeerClient(url, timeout=20.0)
        assert client._session is None
        async with client:
            held = client._session
            assert held is not None
            for _ in range(OPERATIONS // 2):
                await client.complete("negotiate", "step0", encode_step0(step0_exchange()))
                await client.complete("receive_turn", "commitment", encode_commitment(commitment()))
                assert client._session is held
        assert client._session is None
        return operations.kinds()

    kinds = asyncio.run(drive())
    assert len(kinds) == OPERATIONS


def test_a_held_session_still_carries_the_per_call_result_and_timeout() -> None:
    """Holding the session changes nothing a caller can observe semantically."""
    _, url = serve()

    async def drive() -> bool:
        await settle(url)
        client = PeerClient(url, timeout=17.0)
        async with client:
            assert client.timeout == 17.0
            return await client.outcome(encode_reveal(reveal()))

    assert asyncio.run(drive()).accepted is True


def test_the_session_closes_once_even_when_the_body_raises() -> None:
    """Deterministic cleanup: no orphan session survives a failure inside."""
    _, url = serve()

    async def drive() -> PeerClient:
        await settle(url)
        client = PeerClient(url, timeout=20.0)
        with pytest.raises(RuntimeError):
            async with client:
                assert client._session is not None
                raise RuntimeError("something inside the session failed")
        return client

    client = asyncio.run(drive())
    assert client._session is None
    assert client._stack is None


def test_a_second_context_on_the_same_client_opens_a_fresh_session() -> None:
    """Re-entering is explicit and never resurrects the previous session."""
    _, url = serve()

    async def drive() -> bool:
        await settle(url)
        client = PeerClient(url, timeout=20.0)
        async with client:
            first = client._session
        async with client:
            second = client._session
        return first is not second

    assert asyncio.run(drive()) is True


def test_closing_a_client_that_was_never_entered_is_a_safe_no_op() -> None:
    """Cleanup must be idempotent: a failed entry leaves nothing to unwind."""
    client = PeerClient("http://127.0.0.1:9/mcp", timeout=1.0)
    assert client._stack is None
    asyncio.run(client.__aexit__(None, None, None))
    assert client._session is None and client._stack is None
