"""The development-only side of a KIT run: what arrives, and what it is worth.

**Authorized for one thing.** The pinned kit peer offers no keyed Step-0 proof -
its terms signature is an unkeyed content agreement - so a run against it is
authorized to play without our source-required keyed gate **because the whole
run is already classified development-only**. That classification is made before
boot and is carried here, so nothing downstream has to remember it.

**There is no fallback into this mode.** A counted run whose HMAC fails does not
become friendly; it fails. The two are different run classes chosen out of band,
and this object only ever exists for the second.

**A friendly never touches the counted runtime.** Inbound KIT traffic is
delivered here - to an inbox and an audit slot - and not into the production
`PeerOperations`, so the counted path is not merely gated but unreached.
"""

import asyncio
from dataclasses import dataclass, field

from .kit_greeting import KitPairing
from .kit_inbox import KitTurnInbox
from .kit_messages import KitAuditReveal, KitTurn
from .run_class import RunClassification


@dataclass(slots=True)
class KitFriendlySession:
    """One development friendly's inbound state, for one opponent."""

    classification: RunClassification
    window: int = 2
    inbox: KitTurnInbox = field(default_factory=KitTurnInbox)
    audit: KitAuditReveal | None = field(default=None)
    audit_arrived: asyncio.Event = field(default_factory=asyncio.Event)
    pairing: KitPairing | None = field(default=None)
    greetings: int = field(default=0)
    greeted: asyncio.Event = field(default_factory=asyncio.Event)

    def open_sub_game(self) -> KitTurnInbox:
        """A fresh inbox for the sub-game about to be played, and nothing shared.

        Fresh per sub-game on purpose: no board, scent, private truth or message
        history crosses a gNN boundary, so late traffic from the previous game
        cannot be mistaken for the current one - the delivery contract sees it
        against a receiver that expects step 1 and refuses it as out of window.
        """
        self.inbox = KitTurnInbox(window=self.window)
        self.audit, self.audit_arrived = None, asyncio.Event()
        self.greeted = asyncio.Event()
        return self.inbox

    def deliver_turn(self, turn: KitTurn) -> None:
        """Offer one inbound half-turn to the delivery contract."""
        self.inbox.offer(turn)

    def deliver_audit(self, reveal: KitAuditReveal) -> None:
        """Record the opponent's disclosed chain and wake whoever waits for it."""
        self.audit = reveal
        self.audit_arrived.set()

    def record_pairing(self, pairing: KitPairing) -> None:
        """Keep the pairing one accepted greeting established. Binds no identity.

        A redelivered greeting for the sub-game we are already on records the
        same pairing again and wakes nobody twice: it must not open a second
        session, a second backend or a second series.
        """
        self.pairing = pairing
        self.greetings += 1
        self.greeted.set()

    async def await_greeting(self, timeout: float) -> KitPairing:
        """Wait until the gateway has routed this sub-game's greeting to us."""
        await asyncio.wait_for(self.greeted.wait(), timeout)
        assert self.pairing is not None
        return self.pairing

    async def await_audit(self, timeout: float) -> KitAuditReveal:
        """Wait for the opponent's reveal, bounded by our own budget."""
        await asyncio.wait_for(self.audit_arrived.wait(), timeout)
        assert self.audit is not None
        return self.audit
