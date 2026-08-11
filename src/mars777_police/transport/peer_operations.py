"""The production `PeerOperations`: nine inbound operations, nine real owners.

Until now the server had no application adapter at all - every integration test
put a double behind it, so "the transport works" never meant "the runtime got
called". This is the adapter, and it is deliberately the thinnest thing that can
be: **authenticate, resolve, delegate**. It decides no policy, holds no game,
config, audit or result state, and computes nothing.

**Authentication comes first, in every method.** `require_peer` runs before the
runtime is even resolved, including for the operations whose owner never reads a
sender - `ConfigLockRuntime`, `TurnProtocolRuntime` and `accept_audit_disclosure`
would happily process a structurally valid message from a stranger, and the
session gate is what stops that. Step-0 is the one exception: it is the operation
that *establishes* the identity, so it binds rather than requires.

**Lifecycle-scoped owners are resolved per call.** `TurnProtocolRuntime` is
terminal at `CONSUMED` and `AuditRuntime` at `COMPLETE`, so a runtime captured in
`__init__` would be a consumed one by the second turn. The providers are called
inside each method, never stored.
"""

from collections.abc import Callable
from dataclasses import dataclass

from ..app.audit_runtime import AuditRuntime
from ..app.peer_final_messages import FinalNonceReveal, ResultAgreement
from ..app.peer_pregame_messages import (
    ConfigLockEvidence,
    ConfigProposal,
    Step0DeclarationExchange,
)
from ..app.peer_turn_messages import Acknowledgement, Commitment, Reveal
from ..app.pregame_session_runtime import PregameSessionRuntime
from ..app.protocol_values import Sha256Digest
from ..app.result_exchange import ResultExchange
from ..app.turn_protocol_runtime import TurnProtocolRuntime
from .handlers import AuditDocument
from .inbound_session import InboundSession


@dataclass(frozen=True, slots=True)
class InboundPeerOperations:
    """Delegation only: injected owners in, application refusals out."""

    pregame: PregameSessionRuntime
    turns: Callable[[], TurnProtocolRuntime]
    audits: Callable[[], AuditRuntime]
    results: ResultExchange

    def on_step0(self, exchange: Step0DeclarationExchange, session: InboundSession) -> None:
        """Verify Step-0, then bind the identity it proved to this session."""
        session.bind(self.pregame.accept_step0(exchange))

    def on_config_proposal(self, proposal: ConfigProposal, session: InboundSession) -> None:
        """Hand the proposal to negotiation with the **session's** sender."""
        peer = session.require_peer()
        self.pregame.accept_proposal(proposal, peer)

    def on_config_lock(self, evidence: ConfigLockEvidence, session: InboundSession) -> None:
        """Delegate; the pregame runtime supplies our own digest, not theirs."""
        session.require_peer()
        self.pregame.accept_lock(evidence)

    def on_commitment(self, commitment: Commitment, session: InboundSession) -> None:
        """Record the peer's sealed digest in the turn that is live now."""
        session.require_peer()
        self.turns().accept_commitment(commitment)

    def on_acknowledgement(self, acknowledgement: Acknowledgement, session: InboundSession) -> None:
        """Record the peer's acknowledgement of our own commitment."""
        session.require_peer()
        self.turns().accept_acknowledgement(acknowledgement)

    def on_reveal(self, reveal: Reveal, session: InboundSession) -> bool:
        """Return the game legality the turn runtime decided, unaltered.

        The `bool` is passed through exactly: an exception is never converted to
        `False`, so `False` keeps meaning "protocol fine, move illegal".
        """
        session.require_peer()
        return self.turns().accept_reveal(reveal)

    def on_final_nonce_reveal(self, disclosure: FinalNonceReveal, session: InboundSession) -> None:
        """Adopt the nonce batch, attributed to the **authenticated** sender."""
        peer = session.require_peer()
        self.audits().accept_final_nonce_reveal(disclosure, peer)

    def on_audit_disclosure(self, document: AuditDocument, session: InboundSession) -> None:
        """Hand the untrusted document to the audit runtime, unparsed."""
        session.require_peer()
        self.audits().accept_audit_disclosure(document)

    def on_result_agreement(
        self, agreement: ResultAgreement, session: InboundSession
    ) -> Sha256Digest:
        """Return the production digest, with the sender the session proved."""
        peer = session.require_peer()
        return self.results.accept_peer_request(agreement, peer)
