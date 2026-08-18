"""The acceptance proof: four pinned calls over real FastMCP HTTP, and back.

Nothing here calls a router function. A test client speaks only the pinned
KIT-shaped public messages over Streamable HTTP, exactly as a stranger's peer
would, and the assertions are about what the **application** received - a
transport that accepted everything and delivered nothing would pass a status
check and fail here.

`RecordingOperations` stands in for the game runtimes on purpose: it is the
seam a production process fills with `InboundPeerOperations`, whose
authentication gate is proved against the production adapter elsewhere and is
deliberately not weakened for this proof.
"""

import asyncio
from typing import Any

import pytest
from fastmcp import Client
from fastmcp.exceptions import ToolError
from kit_session_support import OUR_GROUP, KitLiveServer, kit_context
from kit_wire_vectors import AUDIT, CONTROL, NEGOTIATION, TURN, turn
from peer_recorder import RecordingOperations

from mars777_police.app.protocol_values import Sha256Digest
from mars777_police.protocol.kit_identity import kit_game_uid, kit_terms_digest

PEER_GROUP = "team-aleph"
TERMS = NEGOTIATION["terms"]
GREETING = NEGOTIATION | {
    "group_id": PEER_GROUP,
    "role": "police",
    "sub_game_number": 1,
    "signature": kit_terms_digest(TERMS, str(NEGOTIATION["nonce"])),
    "game_uid": kit_game_uid(TERMS, OUR_GROUP, PEER_GROUP),
}
"""A greeting our context accepts: same terms, and a signature over those bytes.

The digest is ours, computed here rather than pasted, because the pinned vector
that proves our construction reproduces the kit's lives beside `kit_vectors` -
repeating it here would test the copy instead of the code.
"""


def exchange(
    calls: tuple[tuple[str, dict[str, Any]], ...],
) -> tuple[list[Any], RecordingOperations]:
    """Make *calls* against a live KIT peer over real HTTP, in one session."""
    operations = RecordingOperations()
    context = kit_context()

    async def run(url: str) -> list[Any]:
        async with Client(url) as client:
            return [(await client.call_tool(tool, argument)).data for tool, argument in calls]

    with KitLiveServer(operations, context) as peer:
        return asyncio.run(run(peer.url)), operations


def test_all_four_pinned_tools_answer_over_real_http_and_deliver_semantics() -> None:
    results, operations = exchange(
        (
            ("negotiate", {"message": GREETING}),
            ("receive_turn", {"message": TURN}),
            ("submit_audit", {"payload": AUDIT}),
            ("receive_control", {"message": CONTROL}),
        )
    )

    assert results == [{"ok": True}] * 4
    assert operations.kinds() == ["commitment", "audit_disclosure"]


def test_the_turn_reaches_the_application_as_our_own_commitment_value() -> None:
    _, operations = exchange(
        (("negotiate", {"message": GREETING}), ("receive_turn", {"message": TURN}))
    )
    name, value = operations.seen[0]

    assert name == "commitment"
    assert value.cursor.sub_game == 1
    assert value.cursor.step == 7
    assert value.h_commit == Sha256Digest("a" * 64)


def test_the_audit_reaches_the_application_as_the_json_native_document() -> None:
    _, operations = exchange(
        (("negotiate", {"message": GREETING}), ("submit_audit", {"payload": AUDIT}))
    )
    name, document = operations.seen[0]

    assert name == "audit_disclosure"
    assert document == AUDIT


def test_a_refused_turn_never_reaches_the_application_over_the_real_wire() -> None:
    """Decided before any state change: a partly applied bad turn cannot be undone."""
    with pytest.raises(ToolError):
        exchange((("receive_turn", {"message": turn(timestamp="")}),))


def test_the_strict_argument_name_is_refused_by_a_kit_process() -> None:
    """One process, one surface. There is no redispatch and no fallback."""
    with pytest.raises(ToolError):
        exchange((("receive_turn", {"request": {"kind": "commitment", "payload": {}}}),))


def test_sending_message_to_submit_audit_is_refused() -> None:
    """The asymmetry is load-bearing, and it holds over the real wire."""
    with pytest.raises(ToolError):
        exchange((("submit_audit", {"message": AUDIT}),))
