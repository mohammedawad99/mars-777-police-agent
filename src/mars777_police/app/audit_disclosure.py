"""Reading an untrusted JSON-native audit document, strictly and defensively.

The document is `dict[str, object]` - the frozen `AuditDocument` shape - and it
arrives from an opponent who may have rewritten it. So every read is typed, no
value is coerced to make hostile data fit, and nothing nested is retained by
reference: `DisclosedTurn` holds immutable scalars and **semantic domain
values** built during parsing, which is what makes a later mutation of the
caller's dict unable to change a verdict already derived.

**This module is where the JSON-native audit core becomes internal values.**
Turning the tagged move object into a `PhysicalAction` belongs here rather than
behind a port: `domain.actions`, `domain.board` and `domain.rules` are inward of
`app`, so their constructors are already legally callable, and the cryptographic
`CommitmentPort` keeps its own responsibility instead of acquiring a JSON
projection. The tag table is closed - `MOVE` and `BARRIER`, nothing else - and
an unrecognised representation is refused rather than normalised.

**Only SHARED-AUDIT-INPUT is read.** `LOG_CONTRACT.md` classifies
`entries[].verified`, `audit.result` and `audit.tampered_step` as
LOCAL-DERIVED-AUDIT, "never accepted as peer evidence" - so this module does not
read them at all. A compatibility document that carries them is not rejected for
carrying them; the fields are simply not inputs, which is the contract's own
"ignored for verdict generation".
"""

from dataclasses import dataclass

from ..domain.actions import BarrierAction, MoveAction, PhysicalAction
from ..domain.board import Position
from ..domain.rules import Move
from .protocol_errors import MalformedMessageError


@dataclass(frozen=True, slots=True)
class DisclosedTurn:
    """One entry's SHARED-AUDIT-INPUT members, as immutable semantic values."""

    step: int
    sub_game: int
    role: str
    move: PhysicalAction
    intent: str
    hint: str
    commit: str
    self_pos: Position
    barriers: tuple[Position, ...]
    config_sha256: str


def _refuse(what: str) -> MalformedMessageError:
    return MalformedMessageError(f"audit disclosure {what}")


def _mapping(value: object, what: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise _refuse(f"{what} is not an object")
    return value


def _text(source: dict[str, object], key: str) -> str:
    value = source.get(key)
    if type(value) is not str or not value:
        raise _refuse(f"has no usable {key!r}")
    return value


def _whole(source: dict[str, object], key: str) -> int:
    value = source.get(key)
    if type(value) is not int:
        raise _refuse(f"has no integer {key!r}")
    return value


def _point(value: object, what: str) -> Position:
    if not isinstance(value, list | tuple) or len(value) != 2:
        raise _refuse(f"{what} is not a two-member position")
    row, col = value
    if type(row) is not int or type(col) is not int:
        raise _refuse(f"{what} is not an integer position")
    return Position(row, col)


def _action(value: object) -> PhysicalAction:
    """The disclosed move as a domain action, or a typed refusal.

    Fail-closed in every direction: exactly the two canonical keys, a closed
    kind table, and no default - an unknown token is refused rather than rounded
    to `STAY`, and a barrier keeps its exact declared cell.
    """
    tagged = _mapping(value, "move")
    if set(tagged) != {"kind", "value"}:
        raise _refuse("move is not the two-key tagged action")
    payload = tagged["value"]
    if tagged["kind"] == "MOVE":
        if type(payload) is not str:
            raise _refuse("move value is not a movement token")
        try:
            return MoveAction(Move(payload))
        except ValueError as failure:
            raise _refuse(f"names no movement {payload!r}") from failure
    if tagged["kind"] == "BARRIER":
        return BarrierAction(_point(payload, "barrier placement"))
    raise _refuse("move names no known action kind")


def identity(document: dict[str, object]) -> tuple[str, str, int, str]:
    """The four SHARED-AUDIT-INPUT identity members, or a typed refusal."""
    return (
        _text(document, "game_id"),
        _text(document, "game_uid"),
        _whole(document, "sub_game"),
        _text(document, "config_sha256"),
    )


def turns(document: dict[str, object]) -> tuple[DisclosedTurn, ...]:
    """Every disclosed entry, copied out as immutable values."""
    listing = document.get("entries")
    if not isinstance(listing, list):
        raise _refuse("has no 'entries' collection")
    disclosed: list[DisclosedTurn] = []
    for item in listing:
        entry = _mapping(item, "entry")
        state = _mapping(entry.get("state"), "entry state")
        barriers = state.get("barriers")
        if not isinstance(barriers, list | tuple):
            raise _refuse("entry state has no barrier list")
        disclosed.append(
            DisclosedTurn(
                step=_whole(entry, "step"),
                sub_game=_whole(entry, "sub_game"),
                role=_text(entry, "role"),
                move=_action(entry.get("move")),
                intent=_text(entry, "intent"),
                hint=_text(entry, "hint"),
                commit=_text(entry, "commit"),
                self_pos=_point(state.get("self_pos"), "entry state self_pos"),
                barriers=tuple(_point(one, "entry state barrier") for one in barriers),
                config_sha256=_text(state, "config_sha256"),
            )
        )
    return tuple(disclosed)
