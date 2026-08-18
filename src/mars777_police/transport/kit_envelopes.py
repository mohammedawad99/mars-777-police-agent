"""The four pinned KIT tool arguments, validated at the boundary.

The tool names and the argument names mirror the pinned kit exactly, **including
the asymmetry**: `negotiate`, `receive_turn` and `receive_control` take
`message`; `submit_audit` takes `payload`. It reads like an inconsistency and it
is load-bearing - a peer that sends `message` to `submit_audit` gets a schema
error at the one moment both sides are trying to agree on a result.

**`extra="ignore"`, and only here.** The pinned turn vector accepts an unknown
key and ignores it; that is the kit's declared extension seam, and a receiver
that refuses it cannot be extended without a flag day. Tolerated is not trusted:
an unknown key reaches no semantic value, so it can mutate nothing. Our strict
envelopes keep `extra="forbid"` unchanged.

Every refusal below is a pinned row of `vectors/turn_message.json`: an empty
`timestamp`, a missing or upper-case `commit`, a stringified intensity, a
negative `step`. A missing required key is **refused, never defaulted** - a
defaulted commit is a move the sender never sealed.
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from ..app.protocol_errors import MalformedMessageError
from .wire_scalars import DigestText, NonEmptyText

KIT_TOOLS: tuple[str, ...] = ("negotiate", "receive_turn", "submit_audit", "receive_control")
"""The pinned public surface, in the kit's own order."""

KIT_ARGUMENT_NAMES: dict[str, str] = {
    "negotiate": "message",
    "receive_turn": "message",
    "submit_audit": "payload",
    "receive_control": "message",
}
"""One argument per tool, and `submit_audit` is the one that is not `message`."""

KIT_OK: dict[str, bool] = {"ok": True}
"""The pinned response object. A refusal cannot ride here; it raises instead."""

KIT_WIRE = ConfigDict(extra="ignore", strict=True)
"""Strict types, tolerant keys - the kit's own combination, nowhere else."""

KitJson = dict[str, object]


class KitTurnMessage(BaseModel):
    """`receive_turn(message)` - one half-turn, six required members."""

    model_config = KIT_WIRE

    step: int = Field(ge=0)
    sender: Literal["police", "thief"]
    hint: str
    smell_grid: dict[str, float]
    commit: DigestText
    timestamp: NonEmptyText
    barrier_placed: list[int] | None = None
    capture_claim: list[int] | None = None
    claim_response: KitJson | None = None
    win_claim: KitJson | None = None


class KitAuditRecord(BaseModel):
    """One revealed record: what was sealed, under which nonce, as which digest."""

    model_config = KIT_WIRE

    payload: KitJson
    nonce: NonEmptyText
    commit: DigestText


class KitAuditPayload(BaseModel):
    """`submit_audit(payload)` - the full chain plus nonces, for us to re-hash."""

    model_config = KIT_WIRE

    sender: Literal["police", "thief"]
    records: list[KitAuditRecord]
    result_claim: Literal["capture", "survival", "timeout", "technical_loss", "tamper_forfeit"]


class KitControlMessage(BaseModel):
    """`receive_control(message)` - a status signal that settles nothing."""

    model_config = KIT_WIRE

    kind: Literal["enable", "status", "restart", "quit"]
    sender: Literal["police", "thief"]
    sub_game_number: int = 1
    status: str = ""
    step_budget: float = 0.0
    payload: KitJson | None = None


class KitNegotiateMessage(BaseModel):
    """`negotiate(message)` - flat signed terms, and every declaration beside them.

    The optional members are `None` by default because omission is silence on
    this wire: the unmodified reference peer declares none of them, and refusing
    a greeting for staying silent forfeits the game to ourselves.
    """

    model_config = KIT_WIRE

    terms: KitJson
    nonce: NonEmptyText
    signature: NonEmptyText
    group_id: NonEmptyText
    role: Literal["police", "thief"] | None = None
    sub_game_number: int | None = None
    identity: KitJson | None = None
    scent_model_sha256: str | None = None
    wire_shape_sha256: str | None = None
    info_mode_sha256: str | None = None
    smell_binding_sha256: str | None = None
    info_mode: str | None = None
    game_uid: str | None = None


def parse_kit[Message: BaseModel](model: type[Message], body: KitJson) -> Message:
    """Check *body* against the pinned shape, or refuse it as the peer's fault.

    A framework validation failure is `E-PROTO-MALFORMED` and never
    `E-LOCAL-DEFECT`: a message we could not understand is a message the sender
    built, and reporting our own defect identity for it would send an honest
    opponent hunting a bug on the wrong side of the wire.
    """
    try:
        return model.model_validate(body)
    except ValidationError as failure:
        raise MalformedMessageError(
            f"a KIT {model.__name__} is malformed: {failure.error_count()} problem(s)",
        ) from None
