"""A peer's committed payload as it arrived, and ours built to be understood.

Two values with opposite jobs, and the asymmetry between them is the design.

**`PeerPayload` assumes nothing.** The pinned kit is explicit that payload key
sets need not match across teams - each side seals its own record and the
opponent re-hashes what it was given - so this holds whatever JSON a lawful
peer sealed, unchanged, purely so its digest can be recomputed over the bytes
that peer actually produced. It is deliberately *not* a `DisclosedTurn`: a
matching digest proves correspondence, never that the contents mean anything.

Reads are exact or absent. A field of the wrong type reads as missing rather
than being coerced, because coercion here would manufacture evidence the peer
never sealed - and evidence is precisely what the audit above is weighing.

**`kit_payload` is generous.** We already hold the step, the sub-game, our
role, the action, the intent, the hint, our own cell and the barriers we
declared, and disclosing them at seal time costs us nothing that the final
audit would not reveal anyway. A peer with a richer verifier can then check us
properly. That is our schema, offered - never a shape we require back.

The nonce is absent by construction: under the KIT codec it is appended after
the canonical payload, so sealing it inside as well would hash it twice and
match nobody.
"""

from dataclasses import dataclass, field
from typing import Any

from ..domain.actions import BarrierAction, PhysicalAction
from ..domain.board import Position
from ..protocol.kit_canonical import require_json_value
from .sealed_record_values import ActorRole, Intent
from .turn_cursor import TurnCursor


def _frozen(value: object) -> Any:
    """A structural copy, so a caller's later mutation cannot rewrite evidence."""
    if isinstance(value, dict):
        return {key: _frozen(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_frozen(item) for item in value]
    return value


@dataclass(frozen=True, slots=True)
class PeerPayload:
    """One peer's committed JSON, retained exactly as received."""

    value: dict[str, object] = field(default_factory=dict)

    def __init__(self, value: dict[str, object]) -> None:
        require_json_value(value)
        object.__setattr__(self, "value", _frozen(value))

    def text(self, key: str) -> str | None:
        """The string at *key*, or `None` when absent or not a string."""
        found = self.value.get(key)
        return found if type(found) is str else None

    def whole(self, key: str) -> int | None:
        """The integer at *key*, or `None` when absent or not an integer."""
        found = self.value.get(key)
        return found if type(found) is int else None


def _move_text(action: PhysicalAction) -> str:
    """The kit's action spelling: `MOVE:<letter>` or `BARRIER:<cell>`."""
    if type(action) is BarrierAction:
        return f"BARRIER:[{action.target.row}, {action.target.col}]"
    return f"MOVE:{action.move}"  # type: ignore[union-attr]


def kit_payload(
    *,
    cursor: TurnCursor,
    role: ActorRole,
    action: PhysicalAction,
    intent: Intent,
    hint: str,
    own_position: Position,
    barriers: tuple[Position, ...],
) -> dict[str, object]:
    """Our committed payload for one turn under the KIT codec."""
    return {
        "step": cursor.step,
        "sub_game": cursor.sub_game,
        "role": role.value,
        "move": _move_text(action),
        "intent": intent.value,
        "hint": hint,
        "position": [own_position.row, own_position.col],
        "barriers": [[one.row, one.col] for one in barriers],
    }
