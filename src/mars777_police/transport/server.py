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
"""

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError

from .envelopes import (
    NegotiateRequest,
    ReceiveControlRequest,
    ReceiveTurnRequest,
    SubmitAuditRequest,
)
from .handlers import PeerOperations
from .router import (
    route_negotiate,
    route_receive_control,
    route_receive_turn,
    route_submit_audit,
)
from .wire_errors import outbound

PEER_TOOLS = ("negotiate", "receive_turn", "submit_audit", "receive_control")
"""The complete public surface. There is no fifth peer tool and no alias."""


def build_server(operations: PeerOperations, name: str = "mars777-peer") -> FastMCP:
    """Return the peer server bound to *operations*, with exactly four tools."""
    server: FastMCP = FastMCP(name, strict_input_validation=True)

    @server.tool
    def negotiate(request: NegotiateRequest) -> None:
        """Step-0, config proposal and config lock."""
        try:
            route_negotiate(operations, request)
        except BaseException as failure:
            raise outbound(failure) from None

    @server.tool
    def receive_turn(request: ReceiveTurnRequest) -> bool | None:
        """Commitment, acknowledgement and reveal.

        The `bool` is returned **only** by `reveal`, and only once every lower
        layer has succeeded. Every failure below leaves by the error channel, so
        `False` can never mean anything but game-illegal.
        """
        try:
            return route_receive_turn(operations, request)
        except BaseException as failure:
            raise outbound(failure) from None

    @server.tool
    def submit_audit(request: SubmitAuditRequest) -> None:
        """The final nonce disclosure and the audit document."""
        try:
            route_submit_audit(operations, request)
        except BaseException as failure:
            raise outbound(failure) from None

    @server.tool
    def receive_control(request: ReceiveControlRequest) -> str:
        """The result agreement, returning `result_sha256` as 64 lowercase hex."""
        try:
            return route_receive_control(operations, request).value
        except BaseException as failure:
            raise outbound(failure) from None

    return server


__all__ = ["PEER_TOOLS", "ToolError", "build_server"]
