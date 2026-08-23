"""The other three KIT messages, both ways: greeting, audit reveal, control.

The greeting's optional members are rendered **only when present** - the pinned
`Negotiation.to_wire()` drops every `None`, and on this wire an absent optional
is silence rather than a declaration of nothing. The turn, audit and control
messages do the opposite and keep their nulls explicit, because their pinned
`to_wire` is `asdict`. Matching each one exactly is cheaper than asking a
stranger to tolerate our variation on a first meeting.

A revealed record crosses whole. It is held as a `PeerPayload` - retained
exactly as received, never coerced - because its only job is to let the digest
be recomputed over the bytes the peer actually sealed.
"""

from ..app.kit_greeting import KitGreeting
from ..app.kit_messages import (
    KitAuditReveal,
    KitControl,
    KitControlKind,
    KitRecord,
    KitResultClaim,
    KitRole,
)
from ..app.kit_payload import PeerPayload
from ..app.protocol_errors import MalformedMessageError
from ..app.protocol_values import Sha256Digest
from .kit_envelopes import (
    KitAuditPayload,
    KitControlMessage,
    KitJson,
    KitNegotiateMessage,
)

LOCK_FAMILIES: tuple[tuple[str, str], ...] = (
    ("scent_model", "scent_model_sha256"),
    ("wire_shape", "wire_shape_sha256"),
    ("info_mode", "info_mode_sha256"),
    ("smell_binding", "smell_binding_sha256"),
)
"""The four declarable locked-model families, and the member each rides in.

The bare-string `info_mode` is deliberately absent: a string and a document hash
are uncomparable, and uncomparable is silence rather than a fifth family.
"""


def _payload(value: KitJson) -> PeerPayload:
    """Retain a peer's object exactly, or refuse what is not JSON-native."""
    try:
        return PeerPayload(value)
    except ValueError as failure:
        raise MalformedMessageError(f"a KIT object is not JSON-native: {failure}") from None


def decode_kit_greeting(wire: KitNegotiateMessage) -> KitGreeting:
    """Rebuild the pre-game greeting, keeping every silence a silence."""
    locks = tuple(
        (family, digest)
        for family, member in LOCK_FAMILIES
        if (digest := getattr(wire, member)) is not None
    )
    return KitGreeting(
        _payload(wire.terms),
        wire.nonce,
        wire.signature,
        wire.group_id,
        None if wire.role is None else KitRole(wire.role),
        wire.sub_game_number,
        None if wire.identity is None else _payload(wire.identity),
        wire.game_uid,
        locks,
    )


def encode_kit_greeting(value: KitGreeting) -> KitJson:
    """Render the greeting, omitting every absent member rather than nulling it."""
    message: KitJson = {
        "terms": dict(value.terms.value),
        "nonce": value.nonce,
        "signature": value.signature,
        "group_id": value.group_id,
    }
    optional: tuple[tuple[str, object | None], ...] = (
        ("role", None if value.role is None else value.role.value),
        ("sub_game_number", value.sub_game_number),
        ("identity", None if value.identity is None else dict(value.identity.value)),
        ("game_uid", value.game_uid),
        *((f"{family}_sha256", value.lock(family)) for family, _ in LOCK_FAMILIES),
    )
    message.update({name: found for name, found in optional if found is not None})
    return message


def decode_kit_audit(wire: KitAuditPayload) -> KitAuditReveal:
    """Rebuild a whole sub-game's revealed chain."""
    return KitAuditReveal(
        KitRole(wire.sender),
        tuple(
            KitRecord(_payload(one.payload), one.nonce, Sha256Digest(one.commit))
            for one in wire.records
        ),
        KitResultClaim(wire.result_claim),
        wire.consensus_sha,
    )


def encode_kit_audit(value: KitAuditReveal) -> KitJson:
    """Render the reveal, adding the settlement digest only when one exists.

    Omission rather than `null`, the same way every other optional member on
    this wire is absent when it has nothing to say.
    """
    message: KitJson = {
        "sender": value.sender.value,
        "records": [
            {"payload": dict(one.payload.value), "nonce": one.nonce, "commit": one.commit.value}
            for one in value.records
        ],
        "result_claim": value.result_claim.value,
    }
    if value.consensus_sha is not None:
        message["consensus_sha"] = value.consensus_sha
    return message


def decode_kit_control(wire: KitControlMessage) -> KitControl:
    """Rebuild a control signal. It carries no game state and settles nothing."""
    return KitControl(
        KitControlKind(wire.kind),
        KitRole(wire.sender),
        wire.sub_game_number,
        wire.status,
        wire.step_budget,
        None if wire.payload is None else _payload(wire.payload),
    )


def encode_kit_control(value: KitControl) -> KitJson:
    """Render a control signal in the pinned six-key shape, nulls explicit."""
    return {
        "kind": value.kind.value,
        "sender": value.sender.value,
        "sub_game_number": value.sub_game_number,
        "status": value.status,
        "step_budget": value.step_budget,
        "payload": None if value.payload is None else dict(value.payload.value),
    }
