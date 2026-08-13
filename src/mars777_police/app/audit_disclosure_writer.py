"""Rendering our own audit disclosure - the exact inverse of the reader.

`audit_disclosure.py` turns an untrusted JSON-native document into semantic
values. This turns our own semantic values back into that same document, and
the two are deliberately kept as a pair: the reader's contract is authoritative,
so a real peer `AuditRuntime` must accept what this emits with nothing adapted
on the way.

**One schema, not a second one.** No bundle, no projection, no wire-only
variant, no base64, no stringified JSON, no path. The shape here is the one
`LOG_CONTRACT.md` froze as the disclosure core and the one the reader already
parses, field for field.

**Every value comes from evidence we sealed.** Identity comes from our own
context and each entry from the retained `SealedTurnRecord`, so nothing a caller
supplies at render time can reach the document. Rendering is pure: it builds a
fresh dictionary each call and keeps no reference to what it returned, which is
what makes a caller's later mutation unable to change what we would disclose
next time.

**Local-derived fields are absent on purpose.** `entries[].verified`,
`audit.result` and `audit.tampered_step` are LOCAL-DERIVED-AUDIT - never peer
evidence - so a producer that emitted them would be asserting a verdict it has
no standing to make. The receiver derives them itself.
"""

from ..domain.actions import BarrierAction, MoveAction, PhysicalAction
from ..domain.board import Position
from .capture_transcript import CaptureRecord
from .outbound_evidence_values import LocalEvidenceContext, SealedTurnRecord
from .sealed_record_values import SealedState

AuditDocument = dict[str, object]
"""The frozen JSON-native audit-disclosure document (O6)."""


def _point(position: Position) -> list[int]:
    """One coordinate in the frozen `[row, col]` form."""
    return [position.row, position.col]


def action_value(action: PhysicalAction) -> dict[str, object]:
    """The tagged two-key action object, exactly as the reader parses it."""
    if isinstance(action, MoveAction):
        return {"kind": "MOVE", "value": action.move.value}
    if isinstance(action, BarrierAction):
        return {"kind": "BARRIER", "value": _point(action.target)}
    raise ValueError(f"action must be a MoveAction or BarrierAction, got {type(action).__name__}")


def state_value(state: SealedState) -> dict[str, object]:
    """The own-known snapshot, in the five frozen keys."""
    return {
        "config_sha256": state.config_sha256.value,
        "self_pos": _point(state.self_pos),
        "barriers": [_point(barrier) for barrier in state.barriers],
        "step": state.step,
        "role": state.role.value,
    }


def entry_value(record: SealedTurnRecord, role: str) -> dict[str, object]:
    """One disclosed turn: the SHARED members, and none of the local ones."""
    return {
        "step": record.cursor.step,
        "sub_game": record.cursor.sub_game,
        "role": role,
        "move": action_value(record.action),
        "intent": record.intent.value,
        "hint": record.hint,
        "commit": record.commit.value,
        "state": state_value(record.state),
    }


def capture_value(record: CaptureRecord) -> dict[str, object]:
    """One capture row: the turn it belongs to, what was asked, what was answered."""
    claim = record.claim
    return {
        "step": record.cursor.step,
        "claim": None if claim is None else [claim.cell.row, claim.cell.col],
        "answer": record.answer.value,
    }


def document(
    context: LocalEvidenceContext,
    records: tuple[SealedTurnRecord, ...],
    capture: tuple[CaptureRecord, ...] = (),
) -> AuditDocument:
    """Render the whole sub-game's disclosure from retained evidence only.

    `capture` is what our own reveals asked and were answered - the rows the
    peer will compare against what it actually replied, so a rewritten story
    fails the cross-check rather than passing quietly.
    """
    return {
        "game_id": context.game_id,
        "game_uid": context.game_uid,
        "sub_game": context.sub_game,
        "config_sha256": context.config_sha256.value,
        "entries": [entry_value(record, context.role.value) for record in records],
        "capture": [capture_value(record) for record in capture],
    }
