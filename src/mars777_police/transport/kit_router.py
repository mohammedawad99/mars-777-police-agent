"""Dispatching a decoded KIT message into the **same** application semantics.

There is no second state machine here and no KIT branch inside a game service.
Where the pinned wire and our own contract mean the same thing, the KIT message
becomes the value the application already takes:

* a turn's sealed half **is** a `Commitment`, once the sub-game the handshake
  established is joined to the step the message numbered;
* an audit reveal **is** the JSON-native audit-disclosure document, which is
  what `on_audit_disclosure` has always accepted.

Two operations reach no runtime, and that is a finding rather than an omission.
A greeting establishes the **pairing** - game_id, game_uid, terms agreement - and
binds no identity, because the pinned message has no place for a keyed proof;
every later operation therefore meets the unchanged authentication gate. A
control signal is a status channel the pinned contract says touches no game
state and is never sealed or scored, so honouring it means answering and
changing nothing a game owner owns.

**A KIT turn carries no action.** Under this wire the action is disclosed only
in the audit, so no `Reveal` can be built from a turn and none is invented.
"""

from ..app.kit_friendly import KitFriendlySession
from ..app.kit_greeting import KitGreeting, KitPairing
from ..app.kit_messages import KitAuditReveal, KitControl, KitTurn
from ..app.kit_session import KitSessionContext
from ..app.protocol_values import Sha256Digest
from .codec_final import decode_result_agreement
from .codec_kit_pregame import encode_kit_audit
from .handlers import PeerOperations
from .inbound_session import InboundSession
from .kit_control_envelope import KitResultAgreementMessage


def route_kit_negotiate(context: KitSessionContext, greeting: KitGreeting) -> KitPairing:
    """Establish the pairing, or refuse it on the record. No identity is bound."""
    pairing = context.accept(greeting)
    friendly = _friendly(context)
    if friendly is not None:
        friendly.record_agreement(greeting)
        friendly.record_pairing(pairing)
    return pairing


def route_kit_turn(
    operations: PeerOperations,
    context: KitSessionContext,
    turn: KitTurn,
    session: InboundSession,
) -> None:
    """Deliver the half-turn: to the friendly session, or to the counted runtime.

    The branch is on the **run class**, decided before boot, and never on what
    the message happens to contain. A development friendly therefore does not
    merely fail the counted authentication gate - it never reaches the runtime
    the gate protects.
    """
    friendly = _friendly(context)
    if friendly is not None:
        friendly.deliver_turn(turn)
        return
    operations.on_commitment(turn.commitment(context.sub_game_number), session)


def route_kit_audit(
    operations: PeerOperations,
    context: KitSessionContext,
    reveal: KitAuditReveal,
    session: InboundSession,
) -> None:
    """Deliver the revealed chain: to the friendly session, or as the document."""
    friendly = _friendly(context)
    if friendly is not None:
        friendly.deliver_audit(reveal)
        return
    operations.on_audit_disclosure(encode_kit_audit(reveal), session)


def route_kit_result_agreement(
    operations: PeerOperations,
    message: KitResultAgreementMessage,
    session: InboundSession,
) -> Sha256Digest:
    """Answer the one control kind with the digest the existing runtime computes.

    Identical to `route_receive_control` on the internal surface, and
    deliberately so: the KIT wire changes how the request arrives, never what it
    means or who decides it.
    """
    return operations.on_result_agreement(decode_result_agreement(message.payload), session)


def route_kit_control(context: KitSessionContext, control: KitControl) -> None:
    """Record a status signal, which is all the pinned contract asks of us."""
    context.last_control = control.kind


def _friendly(context: KitSessionContext) -> KitFriendlySession | None:
    """The development session this context carries, if this run is one."""
    friendly = context.friendly
    return friendly if isinstance(friendly, KitFriendlySession) else None
