"""KIT semantic values built from our own authorities, for the wire tests.

Nothing here reads a kit module. Every value is constructed from the project's
own types and every *expected* wire shape lives in `kit_wire_vectors`, which is
the kit's - so a test compares our construction against the kit's publication
rather than against itself.
"""

from mars777_police.app.capture_values import CaptureClaim
from mars777_police.app.kit_greeting import KitGreeting
from mars777_police.app.kit_messages import (
    KitAuditReveal,
    KitClaimResponse,
    KitControl,
    KitControlKind,
    KitRecord,
    KitResultClaim,
    KitRole,
    KitTurn,
)
from mars777_police.app.kit_payload import PeerPayload
from mars777_police.app.protocol_values import Sha256Digest
from mars777_police.domain.board import Position

COMMIT = Sha256Digest("a" * 64)
NONCE = "a1a2a3a4b1b2b3b4c1c2c3c4d1d2d3d4"
TERMS = {"grid_size": 10, "max_steps": 35}
OUR_GROUP = "MaRs-777"
PEER_GROUP = "team-aleph"


def kit_turn(**changes: object) -> KitTurn:
    """The pinned accepted turn, as our own semantic value."""
    fields: dict[str, object] = {
        "step": 7,
        "sender": KitRole.POLICE,
        "hint": "north of the park",
        "smell_grid": (("3,3", 0.9), ("3,4", 0.5), ("4,3", 0.5)),
        "commit": COMMIT,
        "timestamp": "2026-08-08T19:00:00Z",
        "barrier_placed": Position(5, 6),
    }
    fields.update(changes)
    return KitTurn(**fields)  # type: ignore[arg-type]


def kit_claim() -> CaptureClaim:
    return CaptureClaim(Position(2, 4))


def kit_response() -> KitClaimResponse:
    return KitClaimResponse(Position(2, 4), False)


def kit_audit() -> KitAuditReveal:
    return KitAuditReveal(
        KitRole.POLICE,
        (KitRecord(PeerPayload({"step": 1, "move": "MOVE:N"}), "0" * 32, COMMIT),),
        KitResultClaim.CAPTURE,
    )


def kit_control(**changes: object) -> KitControl:
    fields: dict[str, object] = {
        "kind": KitControlKind.STATUS,
        "sender": KitRole.POLICE,
        "sub_game_number": 1,
        "status": "ready",
        "step_budget": 0.0,
    }
    fields.update(changes)
    return KitControl(**fields)  # type: ignore[arg-type]


def kit_greeting(**changes: object) -> KitGreeting:
    fields: dict[str, object] = {
        "terms": PeerPayload(TERMS),
        "nonce": NONCE,
        "signature": "b" * 64,
        "group_id": PEER_GROUP,
        "role": KitRole.POLICE,
        "sub_game_number": 1,
    }
    fields.update(changes)
    return KitGreeting(**fields)  # type: ignore[arg-type]
