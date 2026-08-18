"""The KIT-profile FastMCP surface: the pinned four tools, and nothing else.

**One process, one surface.** This registration is built only when the operator
selected the external mode before boot; the strict registration is built only
when they did not. Nothing here inspects a payload to decide which family
arrived, and there is no fallback from one to the other - a peer that guessed
wrong gets a schema error, which is a diagnosis, where a fallback would be a
silent downgrade.

**The published argument is the kit's own `dict`.** The pinned tools declare
`message: dict` / `payload: dict`, so that is what we publish: a stranger
reading our `tools/list` sees the schema it already knows how to satisfy. The
shape is checked immediately, inside the handler, against the pinned message
models - framework validation at the boundary, semantic core untouched.

**A refusal cannot be a return value.** Every pinned tool answers `{"ok": True}`,
so anything wrong raises and reaches the caller as a tool error rather than
being smuggled back as a false success.

No identity is bound by any of these tools. The pinned greeting carries no keyed
proof, so `negotiate` establishes a pairing and leaves the session
unauthenticated - and the unchanged application gate refuses every operation
that needs one.
"""

from fastmcp import Context, FastMCP

from ..app.kit_session import KitSessionContext
from .codec_kit_pregame import decode_kit_audit, decode_kit_control, decode_kit_greeting
from .codec_kit_turn import decode_kit_turn
from .handlers import PeerOperations
from .kit_envelopes import (
    KIT_OK,
    KitAuditPayload,
    KitControlMessage,
    KitJson,
    KitNegotiateMessage,
    KitTurnMessage,
    parse_kit,
)
from .kit_router import route_kit_audit, route_kit_control, route_kit_negotiate, route_kit_turn
from .session_state import inbound
from .wire_errors import outbound


def build_kit_tools(operations: PeerOperations, context: KitSessionContext, name: str) -> FastMCP:
    """Return a peer server speaking the pinned kit wire, and only that wire."""
    server: FastMCP = FastMCP(name, strict_input_validation=True)

    @server.tool
    async def negotiate(message: KitJson) -> dict[str, bool]:
        """The pre-game gate: flat signed terms, pairing and locked declarations."""
        try:
            greeting = decode_kit_greeting(parse_kit(KitNegotiateMessage, message))
            route_kit_negotiate(context, greeting)
        except BaseException as failure:
            raise outbound(failure) from None
        return KIT_OK

    @server.tool
    async def receive_turn(message: KitJson, session: Context) -> dict[str, bool]:
        """One half-turn: the sealed commit, and the adjuncts it rides with."""
        bound = await inbound(session)
        try:
            turn = decode_kit_turn(parse_kit(KitTurnMessage, message))
            route_kit_turn(operations, context, turn, bound)
        except BaseException as failure:
            raise outbound(failure) from None
        return KIT_OK

    @server.tool
    async def submit_audit(payload: KitJson, session: Context) -> dict[str, bool]:
        """The end-of-sub-game reveal: every record with its nonce, for us to re-hash."""
        bound = await inbound(session)
        try:
            reveal = decode_kit_audit(parse_kit(KitAuditPayload, payload))
            route_kit_audit(operations, reveal, bound)
        except BaseException as failure:
            raise outbound(failure) from None
        return KIT_OK

    @server.tool
    async def receive_control(message: KitJson) -> dict[str, bool]:
        """A status signal. It touches no game state and settles nothing."""
        try:
            route_kit_control(context, decode_kit_control(parse_kit(KitControlMessage, message)))
        except BaseException as failure:
            raise outbound(failure) from None
        return KIT_OK

    return server
