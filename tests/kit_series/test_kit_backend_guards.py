"""The two guards standing between a friendly backend and a counted claim.

A chain whose bytes do not reproduce is refused by our own crypto gate rather
than by the peer's goodwill, and the friendly router branch never reaches the
counted runtime at all - unreachable, not merely gated.
"""

import asyncio

from fastmcp import Client
from kit_backend_doubles import _peer_reveal, _wire_turn
from kit_wire_vectors import COMMIT
from peer_recorder import RecordingOperations

from mars777_police.__main__ import ROLE
from mars777_police.app.commitment_codecs import CommitmentCodec
from mars777_police.app.kit_friendly import KitFriendlySession
from mars777_police.app.kit_messages import (
    KitAuditReveal,
    KitRecord,
    KitResultClaim,
    KitRole,
)
from mars777_police.app.kit_payload import PeerPayload
from mars777_police.app.kit_peer_audit import peer_chain_verified
from mars777_police.app.kit_session import KitSessionContext
from mars777_police.app.protocol_values import Sha256Digest
from mars777_police.app.run_class import RunClassification

OURS = KitRole(ROLE.value)
THEIRS = KitRole.THIEF if OURS is KitRole.POLICE else KitRole.POLICE
TERMS: dict[str, object] = {"board_size": 7, "max_steps": 35}


def test_our_crypto_gate_refuses_a_chain_whose_bytes_do_not_reproduce() -> None:
    tampered = KitAuditReveal(
        THEIRS,
        (KitRecord(PeerPayload({"step": 1}), "0" * 32, Sha256Digest(COMMIT)),),
        KitResultClaim.SURVIVAL,
    )

    assert peer_chain_verified(_peer_reveal(), 1, CommitmentCodec.KIT_CORE_COMMITMENT_V1) is True
    assert peer_chain_verified(tampered, 1, CommitmentCodec.KIT_CORE_COMMITMENT_V1) is False


def test_the_friendly_router_branch_never_reaches_the_counted_runtime() -> None:
    """A friendly does not merely fail the counted gate - it never reaches it."""
    from mars777_police.transport.server import build_server
    from mars777_police.transport.transport_profiles import TransportEnvelopeProfile

    friendly = KitFriendlySession(RunClassification.friendly(kit_terms_agreement=True))
    context = KitSessionContext("MaRs-777", OURS, PeerPayload(TERMS), 1, friendly=friendly)
    operations = RecordingOperations()
    server = build_server(
        operations, profile=TransportEnvelopeProfile.KIT_EXTERNAL, context=context
    )

    async def run() -> None:
        async with Client(server) as client:
            await client.call_tool("receive_turn", {"message": _wire_turn()})
            await client.call_tool(
                "submit_audit",
                {"payload": {"sender": THEIRS.value, "records": [], "result_claim": "survival"}},
            )

    asyncio.run(run())

    assert operations.seen == []
    assert friendly.audit is not None
    assert friendly.inbox.played == {1: COMMIT}
