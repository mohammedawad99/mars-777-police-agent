"""What an outbound call is *named* and *shaped* like, per transport profile.

Split out of `transport/client.py` deliberately. That module owns the endpoint,
the held session and the deadline authority - FIX1/FIX2 - and none of that
changes when the wire does. Argument construction is what changes, so it lives
here, and the client is left holding exactly one thing per call: a tool name and
a dictionary someone else built.

**One message type, one tool, one argument name.** The KIT side dispatches on
the semantic value rather than on a string the caller passes in, which is what
makes the pinned asymmetry unforgeable: an audit reveal can only ever be sent to
`submit_audit`, and it can only ever be sent as `payload`.

The strict rendering is byte-identical to what it always was. A KIT profile that
moved one byte of the internal wire would have broken the exact-six series it
was supposed to leave alone.
"""

from collections.abc import Callable
from typing import Any

from pydantic import BaseModel

from ..app.kit_greeting import KitGreeting
from ..app.kit_messages import KitAuditReveal, KitControl, KitTurn
from ..app.protocol_errors import LocalDefectError
from .codec_kit_pregame import encode_kit_audit, encode_kit_control, encode_kit_greeting
from .codec_kit_turn import encode_kit_turn
from .kit_envelopes import KIT_ARGUMENT_NAMES, KitJson
from .transport_profiles import TransportEnvelopeProfile

KitOutbound = KitGreeting | KitTurn | KitAuditReveal | KitControl
"""Every message this build can put on the pinned kit wire."""

_KIT_CALLS: dict[type, tuple[str, Callable[[Any], KitJson]]] = {
    KitGreeting: ("negotiate", encode_kit_greeting),
    KitTurn: ("receive_turn", encode_kit_turn),
    KitAuditReveal: ("submit_audit", encode_kit_audit),
    KitControl: ("receive_control", encode_kit_control),
}
"""Type in, tool out. A table rather than a chain, so the mapping is total and
the pinned asymmetry cannot be spelled wrong at a call site."""


def wire_json(model: BaseModel) -> KitJson:
    """Render a DTO for the wire, **omitting** every absent member.

    `exclude_none=True` is the contract, not a convenience: a member that is
    absent must not arrive as `null`. That is what keeps a CPU-only
    participant's `vram_gb` out of the authenticated Step-0 core entirely.
    """
    return model.model_dump(mode="json", exclude_none=True)


def _require(profile: TransportEnvelopeProfile, expected: TransportEnvelopeProfile) -> None:
    """Refuse to build the other profile's arguments, rather than send them.

    A process that could construct both shapes could send the wrong one, and a
    peer receiving it has no way to tell a mistake from a downgrade attempt.
    """
    if profile is not expected:
        raise LocalDefectError(
            f"a {profile.value} transport cannot build {expected.value} arguments",
        )


def strict_arguments(
    kind: str,
    payload: BaseModel | KitJson,
    profile: TransportEnvelopeProfile = TransportEnvelopeProfile.STRICT_PROJECT,
) -> KitJson:
    """Build the one frozen internal argument: `request = {kind, payload}`."""
    _require(profile, TransportEnvelopeProfile.STRICT_PROJECT)
    body = wire_json(payload) if isinstance(payload, BaseModel) else payload
    return {"request": {"kind": kind, "payload": body}}


def kit_call(
    message: KitOutbound,
    profile: TransportEnvelopeProfile = TransportEnvelopeProfile.KIT_EXTERNAL,
) -> tuple[str, KitJson]:
    """The tool name and the exact arguments *message* is sent as."""
    _require(profile, TransportEnvelopeProfile.KIT_EXTERNAL)
    tool, encode = _KIT_CALLS[type(message)]
    return tool, {KIT_ARGUMENT_NAMES[tool]: encode(message)}
