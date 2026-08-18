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

from ..app.kit_greeting import KitGreeting, KitPairing
from ..app.kit_messages import KitAuditReveal, KitControl, KitTurn
from ..app.kit_session import KitSessionContext
from .codec_kit_pregame import encode_kit_audit
from .handlers import PeerOperations
from .inbound_session import InboundSession


def route_kit_negotiate(context: KitSessionContext, greeting: KitGreeting) -> KitPairing:
    """Establish the pairing, or refuse it on the record. No identity is bound."""
    return context.accept(greeting)


def route_kit_turn(
    operations: PeerOperations,
    context: KitSessionContext,
    turn: KitTurn,
    session: InboundSession,
) -> None:
    """Deliver the sealed half as the commitment our application already takes."""
    operations.on_commitment(turn.commitment(context.sub_game_number), session)


def route_kit_audit(
    operations: PeerOperations, reveal: KitAuditReveal, session: InboundSession
) -> None:
    """Deliver the revealed chain as the JSON-native disclosure document."""
    operations.on_audit_disclosure(encode_kit_audit(reveal), session)


def route_kit_control(context: KitSessionContext, control: KitControl) -> None:
    """Record a status signal, which is all the pinned contract asks of us."""
    context.last_control = control.kind
