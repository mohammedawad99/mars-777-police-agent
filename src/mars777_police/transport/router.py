"""Dispatching a validated envelope to the application, and nothing else.

Five steps, in order: the framework has already validated the envelope against
the tool's own closed `kind` set, so this module decodes the payload to its
semantic value, calls the application handler, and returns the exact
operation-specific result. It holds **no state**, decides **no policy**, and
contains no second state machine.

Dispatch is by explicit `kind`, never by inspecting which payload keys happen to
be present. A valid kind on the wrong tool never reaches here at all - the tool's
schema refuses it - which is what the frozen contract requires.
"""

from ..app.protocol_values import Sha256Digest
from .codec_declaration import decode_step0
from .codec_final import decode_final_nonce, decode_result_agreement
from .codec_pregame import decode_lock, decode_proposal
from .codec_turn import decode_acknowledgement, decode_commitment, decode_reveal
from .envelopes import (
    NegotiateRequest,
    ReceiveControlRequest,
    ReceiveTurnRequest,
    SubmitAuditRequest,
)
from .handlers import PeerOperations


def route_negotiate(operations: PeerOperations, request: NegotiateRequest) -> None:
    """Step-0, config proposal or config lock - all ordinary completion."""
    if request.kind == "step0":
        operations.on_step0(decode_step0(request.payload))
    elif request.kind == "config_proposal":
        operations.on_config_proposal(decode_proposal(request.payload))
    else:
        operations.on_config_lock(decode_lock(request.payload))


def route_receive_turn(operations: PeerOperations, request: ReceiveTurnRequest) -> bool | None:
    """Commitment and acknowledgement complete; reveal returns its legality."""
    if request.kind == "commitment":
        operations.on_commitment(decode_commitment(request.payload))
        return None
    if request.kind == "acknowledgement":
        operations.on_acknowledgement(decode_acknowledgement(request.payload))
        return None
    return operations.on_reveal(decode_reveal(request.payload))


def route_submit_audit(operations: PeerOperations, request: SubmitAuditRequest) -> None:
    """The nonce disclosure and the audit document - both ordinary completion.

    No verdict crosses in either direction: `FinalAuditVerdict` stays local and
    no acknowledgement family exists.
    """
    if request.kind == "final_nonce_reveal":
        operations.on_final_nonce_reveal(decode_final_nonce(request.payload))
    else:
        operations.on_audit_disclosure(request.payload)


def route_receive_control(
    operations: PeerOperations, request: ReceiveControlRequest
) -> Sha256Digest:
    """The one control kind, returning the frozen `Sha256Digest` result."""
    return operations.on_result_agreement(decode_result_agreement(request.payload))
