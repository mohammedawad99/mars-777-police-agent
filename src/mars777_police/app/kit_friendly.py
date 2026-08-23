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
from .protocol_errors import LocalDefectError
from .run_class import RunClassification


@dataclass(slots=True)
class KitFriendlySession:
    """One development friendly's inbound state, for one opponent."""

    classification: RunClassification
    window: int = 2
    inbox: KitTurnInbox = field(default_factory=KitTurnInbox)
    audit: KitAuditReveal | None = field(default=None)
    audit_arrived: asyncio.Event = field(default_factory=asyncio.Event)
    settlement: KitAuditReveal | None = field(default=None)
    """The peer's series settlement. It belongs to the series, not to a sub-game.

    Deliberately **not** cleared by `open_sub_game`: it can legitimately arrive
    while the last sub-game is still draining, and a per-sub-game reset would
    discard the one message the whole series has to end on.
    """

    settled_arrived: asyncio.Event = field(default_factory=asyncio.Event)
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
        """Record a disclosure, keeping the series settlement out of the sub-game slot.

        The peer sends both a sub-game chain and the final series settlement
        through `submit_audit`, so one delivery point receives two different
        kinds of message. A settlement placed in the sub-game slot would be
        re-hashed as a chain, fail for carrying no records, and be reported as
        the opponent's tamper - which is the opposite of what it says.
        """
        if reveal.settles_the_series:
            self.settlement = reveal
            self.settled_arrived.set()
            return
        self.audit = reveal
        self.audit_arrived.set()

    def take_settlement(self) -> KitAuditReveal | None:
        """The peer's settlement if one has arrived, without waiting for it.

        The exchange polls rather than blocks: it has to keep resending our own
        envelope on the agreed cadence, and a blocking wait would stop it doing
        the half the peer is waiting for.
        """
        return self.settlement

    async def await_settlement(self, timeout: float) -> KitAuditReveal:
        """Wait for the peer's series settlement, bounded by the agreed window.

        Bounded by the pairing's own `consensus_timeout_sec` rather than by a
        turn budget: this arrives after the last sub-game is already disclosed,
        and the two sides reach it at different moments.
        """
        await asyncio.wait_for(self.settled_arrived.wait(), timeout)
        settlement = self.settlement
        if settlement is None:  # pragma: no cover - the event is only set with one
            raise LocalDefectError("a settlement event fired with no settlement behind it")
        return settlement

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
