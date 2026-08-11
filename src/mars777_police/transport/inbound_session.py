"""The authenticated peer identity of one inbound FastMCP session.

Stage 5-R3 proved why this has to exist. Three application owners require an
**authenticated** sender, the frozen contracts deliberately keep it out of the
message - `DECLARATION_CONTRACT.md` R14-R1-5: *"No `sender_id` is added to
`Declaration`"*, and `RESULT_CONTRACT.md` R13-R1-8 makes it *"the authenticated
sender identity"* - and deriving it from the payload turns
`sender_id != request.contribution.group_id` into `x != x`. So the identity is
established from the transport session instead, and never from what the caller
said about itself.

**One session, one optional group id, and nothing else.** This is not a
registry: it holds no runtime, no declaration, no config and no game state. A
store that could hold those would be the service locator `DEPENDENCY_RULES.md`
D3 forbids, and it would let one peer's call reach another peer's runtime.

**FastMCP-free by construction.** The session id and the identity arrive as
plain strings from the server adapter, so no framework type crosses into `app`
and this value can be built in a test without a server. `pending` is the
write-back the server flushes to session state *after* the operation succeeded -
which is what makes a failed Step-0 leave the session unbound.
"""

from dataclasses import dataclass, field

from ..app.protocol_errors import AuthFailureError


@dataclass(slots=True)
class InboundSession:
    """One inbound session: who it is, if Step-0 has proved that yet."""

    session_id: str
    peer: str | None = field(default=None)
    pending: str | None = field(default=None)

    @property
    def is_authenticated(self) -> bool:
        """Whether a successful Step-0 has bound an identity to this session."""
        return self.peer is not None

    def require_peer(self) -> str:
        """Return the authenticated identity, or refuse the operation.

        Every post-Step-0 operation goes through here, including the ones whose
        application owner never reads the sender: a structurally valid payload
        on an unauthenticated session must not reach a live runtime.
        """
        peer = self.peer
        if peer is None:
            raise AuthFailureError(
                "this session has not completed an authenticated Step-0",
            )
        return peer

    def bind(self, peer: str) -> None:
        """Bind *peer* to this session after Step-0 verified it.

        Rebinding to a *different* identity is refused: a session that proved it
        was one peer must never become another, whatever a later payload claims.
        """
        if self.peer is not None and self.peer != peer:
            raise AuthFailureError(
                "an authenticated session cannot be rebound to a different peer",
            )
        self.peer = peer
        self.pending = peer
