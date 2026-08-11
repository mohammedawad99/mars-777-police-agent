"""Codec for the three per-turn peer families.

The action tag maps through an **explicit closed table**: `"MOVE"` and
`"BARRIER"` are the only accepted tags, and an unrecognised one raises the
malformed identity rather than reaching a domain constructor. A movement token
becomes a `Move` here, at the protocol boundary - the domain never guesses.

`Reveal` carries no nonce in either direction, because the nonce is withheld
until final audit; the nonces travel exactly once, through `codec_final`.
"""

from ..app.peer_turn_messages import Acknowledgement, Commitment, Reveal
from ..app.protocol_errors import MalformedMessageError
from ..app.protocol_values import Sha256Digest
from ..app.turn_cursor import TurnCursor
from ..domain.actions import BarrierAction, MoveAction, PhysicalAction
from ..domain.board import Position
from ..domain.rules import Move
from .wire_turn import (
    AcknowledgementWire,
    ActionWire,
    BarrierActionWire,
    CommitmentWire,
    MoveActionWire,
    RevealWire,
    TurnCursorWire,
)


def _cursor(wire: TurnCursorWire) -> TurnCursor:
    return TurnCursor(wire.sub_game, wire.step)


def _cursor_wire(cursor: TurnCursor) -> TurnCursorWire:
    return TurnCursorWire(sub_game=cursor.sub_game, step=cursor.step)


def decode_action(wire: ActionWire) -> PhysicalAction:
    """Map the tagged action to its domain value, refusing anything else."""
    if isinstance(wire, MoveActionWire):
        try:
            return MoveAction(Move(wire.value))
        except ValueError as failure:
            raise MalformedMessageError(f"unknown move token {wire.value!r}") from failure
    return BarrierAction(Position(wire.value[0], wire.value[1]))


def encode_action(action: PhysicalAction) -> ActionWire:
    """Render the action with the same two-key tagged shape."""
    if isinstance(action, MoveAction):
        return MoveActionWire(kind="MOVE", value=action.move.value)
    return BarrierActionWire(kind="BARRIER", value=[action.target.row, action.target.col])


def decode_commitment(wire: CommitmentWire) -> Commitment:
    """Rebuild a commitment."""
    return Commitment(_cursor(wire.cursor), Sha256Digest(wire.h_commit))


def encode_commitment(value: Commitment) -> CommitmentWire:
    """Render a commitment."""
    return CommitmentWire(cursor=_cursor_wire(value.cursor), h_commit=value.h_commit.value)


def decode_acknowledgement(wire: AcknowledgementWire) -> Acknowledgement:
    """Rebuild an acknowledgement - the exact existing contract, no `accepted`."""
    return Acknowledgement(_cursor(wire.cursor), Sha256Digest(wire.h_commit))


def encode_acknowledgement(value: Acknowledgement) -> AcknowledgementWire:
    """Render an acknowledgement."""
    return AcknowledgementWire(cursor=_cursor_wire(value.cursor), h_commit=value.h_commit.value)


def decode_reveal(wire: RevealWire) -> Reveal:
    """Rebuild a reveal. Legality is the operation result, never a member."""
    return Reveal(_cursor(wire.cursor), decode_action(wire.action), wire.hint)


def encode_reveal(value: Reveal) -> RevealWire:
    """Render a reveal."""
    return RevealWire(
        cursor=_cursor_wire(value.cursor), action=encode_action(value.action), hint=value.hint
    )
