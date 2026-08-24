"""What `receive_control` may carry on the KIT wire: a status signal, or the result.

The pinned kit uses `receive_control` for a status signal with a closed
four-word vocabulary that settles nothing. This project's own frozen matrix
already pairs the same tool with exactly one semantic kind - `result_agreement` -
and `TOOL_KINDS` has said so since the internal wire was frozen. Stage 9C makes
that one kind reachable on the external surface too, so an alternating counted
series can complete the agreement its result artifact depends on.

**Nothing new is invented here.** No fifth tool, no tenth kind, no second
message family: the payload is the existing `ResultAgreementWire`, decoded by the
existing codec, answered by the existing runtime, and digested by the existing
`ResultDigester`.

**The two forms are told apart by the discriminator that already exists.**
`kind` is a required member of the pinned control message, so the union keys on
it rather than sniffing for a payload shape. A body whose `kind` is neither the
kit's four words nor `result_agreement` matches no member and is refused - the
legacy vocabulary keeps its exact meaning, and a peer that sends the old form
still gets the old answer.

**Refusal is the default.** A malformed body raises `MalformedMessageError`
before any state is read or written, so an unparseable or unknown control form
can never reach - let alone mutate - the result agreement.
"""

from typing import Annotated, Literal

from pydantic import BaseModel, Field, TypeAdapter, ValidationError

from ..app.protocol_errors import MalformedMessageError
from .kit_envelopes import KIT_WIRE, KitControlMessage, KitJson
from .wire_final import ResultAgreementWire


class KitResultAgreementMessage(BaseModel):
    """`receive_control(message)` carrying the one existing result agreement.

    The payload is `ResultAgreementWire` verbatim - the same model the internal
    surface carries - so the sender's own `ResultContribution` travels with it
    and is validated by the same authority on both wires.
    """

    model_config = KIT_WIRE

    kind: Literal["result_agreement"]
    payload: ResultAgreementWire


KitControlEnvelope = Annotated[
    KitControlMessage | KitResultAgreementMessage,
    Field(discriminator="kind"),
]
"""Either control form, told apart by the `kind` the pinned message already has."""

_CONTROL = TypeAdapter[KitControlMessage | KitResultAgreementMessage](KitControlEnvelope)


def parse_kit_control(body: KitJson) -> KitControlMessage | KitResultAgreementMessage:
    """Return whichever control form *body* is, or refuse it as the sender's fault.

    A framework validation failure is `E-PROTO-MALFORMED` and never
    `E-LOCAL-DEFECT`, for the same reason `parse_kit` says so: a message we could
    not understand is a message the sender built.
    """
    try:
        return _CONTROL.validate_python(body)
    except ValidationError as failure:
        raise MalformedMessageError(
            f"a KIT control message is malformed: {failure.error_count()} problem(s)",
        ) from None
