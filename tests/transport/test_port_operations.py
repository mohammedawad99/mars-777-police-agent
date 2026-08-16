"""Every outbound port operation, driven against a real FastMCP server.

The adapter is the only thing between a semantic value and the wire, so each of
the nine operations is exercised end to end rather than merely declared - and
the assertion is what the **application** received, in order.
"""

import asyncio
import threading

import uvicorn
from peer_ops import (
    acknowledgement,
    agreement,
    audit_document,
    commitment,
    final_nonce,
    lock_evidence,
    proposal,
    reveal,
    step0_exchange,
)
from peer_process import free_port
from peer_recorder import RecordingOperations

from mars777_police.app.peer_supervision import PeerDeadline, TimeoutPolicy
from mars777_police.transport.client import PeerClient
from mars777_police.transport.peer_transport import FastMcpPeerTransport
from mars777_police.transport.server import build_server


def test_every_port_operation_reaches_the_application_through_the_adapter() -> None:
    """Drive all nine outbound operations against a real in-process server.

    The adapter is the only thing between a semantic value and the wire, so
    each method is exercised end to end rather than merely declared.
    """
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

    async def drive() -> bool:
        for _ in range(400):
            if server.started:
                break
            await asyncio.sleep(0.05)
        adapter = FastMcpPeerTransport(
            PeerClient(f"http://127.0.0.1:{port}/mcp", PeerDeadline(TimeoutPolicy(20.0)))
        )
        await adapter.send_step0(step0_exchange())
        await adapter.send_config_proposal(proposal())
        await adapter.send_config_lock(lock_evidence())
        await adapter.send_commitment(commitment())
        await adapter.send_acknowledgement(acknowledgement())
        legal = await adapter.send_reveal(reveal())
        await adapter.send_final_nonce_reveal(final_nonce())
        await adapter.send_audit_disclosure(audit_document())
        digest = await adapter.send_result_agreement(agreement())
        assert len(digest.value) == 64
        return legal

    try:
        assert asyncio.run(drive()).accepted is True
    finally:
        server.should_exit = True
    assert operations.kinds() == [
        "step0",
        "config_proposal",
        "config_lock",
        "commitment",
        "acknowledgement",
        "reveal",
        "final_nonce_reveal",
        "audit_disclosure",
        "result_agreement",
    ]
