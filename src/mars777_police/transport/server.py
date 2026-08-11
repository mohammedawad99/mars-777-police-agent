"""The FastMCP server adapter: one stable ingress per peer process.

**Exactly four public tools**, matching the frozen names. Not a server per game,
per sub-game or per turn - the declaration's `mcp_endpoint` names this process,
and it stays put for the whole series.

The server owns wire parsing, route selection, invoking the application handler,
encoding the result and translating failures. It owns **no** game state: the
authority stays in the application runtime it was handed.

`strict_input_validation=True` is not decoration. Without it the boundary would
lean on Pydantic's lenient coercion, and a JSON number where canonical decimal
text belongs would silently become a `Decimal` with different bytes.

The Streamable HTTP application is obtained from the returned server with
`.http_app(path=...)`; no wrapper is provided for it, because a wrapper that
only forwards is one more thing to keep true.

**The authenticated peer identity lives in FastMCP's own session state.** The
tools are `async` only for that: `Context.get_state`/`set_state` are
session-scoped and persist across `call_tool` on one Streamable-HTTP session,
and `Context` never appears in a published tool schema, so the wire contract is
untouched and the client cannot supply its own identity. The write-back happens
**after** the operation returned - a Step-0 that raises leaves the session
exactly as unauthenticated as it found it.
"""

from fastmcp import Context, FastMCP
from fastmcp.exceptions import ToolError

from .envelopes import (
    NegotiateRequest,
    ReceiveControlRequest,
    ReceiveTurnRequest,
    SubmitAuditRequest,
)
from .handlers import PeerOperations
from .inbound_session import InboundSession
from .router import (
    route_negotiate,
    route_receive_control,
    route_receive_turn,
    route_submit_audit,
)
from .wire_errors import outbound

PEER_TOOLS = ("negotiate", "receive_turn", "submit_audit", "receive_control")
"""The complete public surface. There is no fifth peer tool and no alias."""

AUTH_STATE_KEY = "mars777.authenticated_peer"
"""The one session-state key: an authenticated `group_id`, and nothing else."""


async def inbound(context: Context) -> InboundSession:
    """Read this session's bound identity, if Step-0 has established one."""
    bound = await context.get_state(AUTH_STATE_KEY)
    return InboundSession(context.session_id, bound if isinstance(bound, str) else None)


async def persist(context: Context, session: InboundSession) -> None:
    """Write back a binding the operation just proved. Failures never reach here."""
    if session.pending is not None:
        await context.set_state(AUTH_STATE_KEY, session.pending)


def build_server(operations: PeerOperations, name: str = "mars777-peer") -> FastMCP:
    """Return the peer server bound to *operations*, with exactly four tools."""
    server: FastMCP = FastMCP(name, strict_input_validation=True)

    @server.tool
    async def negotiate(request: NegotiateRequest, context: Context) -> None:
        """Step-0, config proposal and config lock."""
        session = await inbound(context)
        try:
            route_negotiate(operations, request, session)
        except BaseException as failure:
            raise outbound(failure) from None
        await persist(context, session)

    @server.tool
    async def receive_turn(request: ReceiveTurnRequest, context: Context) -> bool | None:
        """Commitment, acknowledgement and reveal.

        The `bool` is returned **only** by `reveal`, and only once every lower
        layer has succeeded. Every failure below leaves by the error channel, so
        `False` can never mean anything but game-illegal.
        """
        session = await inbound(context)
        try:
            return route_receive_turn(operations, request, session)
        except BaseException as failure:
            raise outbound(failure) from None

    @server.tool
    async def submit_audit(request: SubmitAuditRequest, context: Context) -> None:
        """The final nonce disclosure and the audit document."""
        session = await inbound(context)
        try:
            route_submit_audit(operations, request, session)
        except BaseException as failure:
            raise outbound(failure) from None

    @server.tool
    async def receive_control(request: ReceiveControlRequest, context: Context) -> str:
        """The result agreement, returning `result_sha256` as 64 lowercase hex."""
        session = await inbound(context)
        try:
            return route_receive_control(operations, request, session).value
        except BaseException as failure:
            raise outbound(failure) from None

    return server


__all__ = ["AUTH_STATE_KEY", "PEER_TOOLS", "ToolError", "build_server", "inbound", "persist"]
