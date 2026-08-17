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
from .audit_json import mapping, point, refuse, text, whole


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


def _action(value: object) -> PhysicalAction:
    """The disclosed move as a domain action, or a typed refusal.

    Fail-closed in every direction: exactly the two canonical keys, a closed
    kind table, and no default - an unknown token is refused rather than rounded
    to `STAY`, and a barrier keeps its exact declared cell.
    """
    tagged = mapping(value, "move")
    if set(tagged) != {"kind", "value"}:
        raise refuse("move is not the two-key tagged action")
    payload = tagged["value"]
    if tagged["kind"] == "MOVE":
        if type(payload) is not str:
            raise refuse("move value is not a movement token")
        try:
            return MoveAction(Move(payload))
        except ValueError as failure:
            raise refuse(f"names no movement {payload!r}") from failure
    if tagged["kind"] == "BARRIER":
        return BarrierAction(point(payload, "barrier placement"))
    raise refuse("move names no known action kind")


def identity(document: dict[str, object]) -> tuple[str, str, int, str]:
    """The four SHARED-AUDIT-INPUT identity members, or a typed refusal."""
    return (
        text(document, "game_id"),
        text(document, "game_uid"),
        whole(document, "sub_game"),
        text(document, "config_sha256"),
    )


def _intent(entry: dict[str, object]) -> str:
    """The one classification this entry carries, however the peer spelled it.

    **C-08, enforced rather than assumed.** The book's English code comment says
    `verdict` and its Hebrew prose says *intent classification*; the two lists
    are position-for-position identical, so they name the same commit-time
    value and the sealed payload carries `intent` alone. The reference
    implementation nonetheless writes both keys with the same value, which is
    lawful - and PRD04-FR-018 requires that when both arrive they agree.

    A contradiction is refused **as a malformed document**, on the refusal path
    every other reader here already uses. It is not tampering, not a technical
    loss and not a sanction: two keys that disagree describe no game at all, and
    accepting either one would be inventing the dual truth C-08 forbids.

    `verdict` remains a non-input in every other respect - absent, it changes
    nothing, and no verdict field is ever added to what we send.
    """
    intent = text(entry, "intent")
    if "verdict" not in entry:
        return intent
    if entry.get("verdict") != intent:
        raise refuse("entry carries a 'verdict' that contradicts its 'intent'")
    return intent


def turns(document: dict[str, object]) -> tuple[DisclosedTurn, ...]:
    """Every disclosed entry, copied out as immutable values."""
    listing = document.get("entries")
    if not isinstance(listing, list):
        raise refuse("has no 'entries' collection")
    disclosed: list[DisclosedTurn] = []
    for item in listing:
        entry = mapping(item, "entry")
        state = mapping(entry.get("state"), "entry state")
        barriers = state.get("barriers")
        if not isinstance(barriers, list | tuple):
            raise refuse("entry state has no barrier list")
        disclosed.append(
            DisclosedTurn(
                step=whole(entry, "step"),
                sub_game=whole(entry, "sub_game"),
                role=text(entry, "role"),
                move=_action(entry.get("move")),
                intent=_intent(entry),
                hint=text(entry, "hint"),
                commit=text(entry, "commit"),
                self_pos=point(state.get("self_pos"), "entry state self_pos"),
                barriers=tuple(point(one, "entry state barrier") for one in barriers),
                config_sha256=text(state, "config_sha256"),
            )
        )
    return tuple(disclosed)
