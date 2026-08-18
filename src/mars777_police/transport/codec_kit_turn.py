"""The KIT turn, both ways: pinned wire object to our value, and back.

Decoding is total and lossless. Every member the pinned wire defines lands in a
semantic value - the sealed `commit` becomes a `Sha256Digest`, the two cells
become `Position`s, the survival claim becomes a bool - and the smell grid is
carried across **unconverted**, because it is the peer's binary64 and our own
physics is exact `Decimal`.

Encoding renders the full ten-key shape with **nulls explicit**, matching the
pinned `TurnMessage.to_wire()` (`asdict`, which keeps `None`). A receiver should
tolerate either form, but a sender that matches the common shape gives the other
side less to guess about on a first meeting.
"""

from ..app.capture_values import CaptureClaim
from ..app.kit_messages import KitClaimResponse, KitRole, KitTurn
from ..app.protocol_errors import MalformedMessageError
from ..app.protocol_values import Sha256Digest
from ..domain.board import Position
from .kit_envelopes import KitJson, KitTurnMessage

SURVIVAL_CLAIM: KitJson = {"type": "survival"}
"""The thief's threshold claim, in the one spelling the pinned wire defines."""


def _cell(pair: list[int] | None) -> Position | None:
    """A `[row, col]` cell, or nothing. Any other length is malformed."""
    if pair is None:
        return None
    if len(pair) != 2:
        raise MalformedMessageError("a KIT cell must carry exactly [row, col]")
    return Position(pair[0], pair[1])


def _response(value: KitJson | None) -> KitClaimResponse | None:
    """`{'claim': [r, c], 'caught': bool}` - the thief's obligatory honest answer."""
    if value is None:
        return None
    claim, caught = value.get("claim"), value.get("caught")
    if not isinstance(claim, list) or type(caught) is not bool:
        raise MalformedMessageError("a KIT claim response needs a [row, col] claim and a bool")
    cell = _cell([int(one) for one in claim])
    if cell is None:  # pragma: no cover - a list is never None
        raise MalformedMessageError("a KIT claim response needs a claim")
    return KitClaimResponse(cell, caught)


def _survival(value: KitJson | None) -> bool:
    """A win claim is the survival claim or it is nothing we will act on."""
    if value is None:
        return False
    if value != SURVIVAL_CLAIM:
        raise MalformedMessageError(f"unknown KIT win claim {value!r}")
    return True


def decode_kit_turn(wire: KitTurnMessage) -> KitTurn:
    """Rebuild one half-turn from the pinned message."""
    claim = _cell(wire.capture_claim)
    return KitTurn(
        wire.step,
        KitRole(wire.sender),
        wire.hint,
        tuple(sorted(wire.smell_grid.items())),
        Sha256Digest(wire.commit),
        wire.timestamp,
        _cell(wire.barrier_placed),
        None if claim is None else CaptureClaim(claim),
        _response(wire.claim_response),
        _survival(wire.win_claim),
    )


def encode_kit_turn(value: KitTurn) -> KitJson:
    """Render one half-turn in the pinned ten-key shape, nulls included."""
    barrier, claim, answer = value.barrier_placed, value.capture_claim, value.claim_response
    return {
        "step": value.step,
        "sender": value.sender.value,
        "commit": value.commit.value,
        "hint": value.hint,
        "smell_grid": dict(value.smell_grid),
        "timestamp": value.timestamp,
        "barrier_placed": None if barrier is None else [barrier.row, barrier.col],
        "capture_claim": None if claim is None else [claim.cell.row, claim.cell.col],
        "claim_response": None
        if answer is None
        else {"claim": [answer.claim.row, answer.claim.col], "caught": answer.caught},
        "win_claim": dict(SURVIVAL_CLAIM) if value.survival_claimed else None,
    }
