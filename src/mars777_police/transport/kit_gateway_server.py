"""The gateway's two FastMCP surfaces: one the opponent sees, one it never does.

The **public** surface is the pinned four tools, byte-identical to the schema a
role backend publishes - the opponent cannot tell it is talking to a router, and
nothing about our role split reaches the wire.

The **private** surface carries exactly one operation, `sub_game_settled`, and is
bound to loopback. It exists because settlement must be *signalled*: HTTP
silence cannot distinguish a peer that is thinking from a sub-game that is
finished, and guessing between them is how a sub-game gets skipped. The backend
that played it says so, and only then may gameplay routing move on.

Private backend endpoints are an implementation detail. They are never
advertised to the opponent and never written into a declaration artifact: the
opponent sees one stable group URL for the whole series.
"""

from fastmcp import FastMCP

from .kit_envelopes import KIT_OK, KitJson
from .kit_gateway import KitGroupGateway
from .wire_errors import outbound

GATEWAY_TOOLS = ("negotiate", "receive_turn", "submit_audit", "receive_control")
"""The public surface, identical to a backend's. The router is invisible."""

ADMIN_TOOLS = ("sub_game_settled",)
"""The private surface, loopback only, and never part of the KIT contract."""


def build_gateway_tools(gateway: KitGroupGateway, name: str = "mars777-group") -> FastMCP:
    """The group's one opponent-facing ingress for a whole alternating series."""
    server: FastMCP = FastMCP(name, strict_input_validation=True)

    @server.tool
    async def negotiate(message: KitJson) -> dict[str, bool]:
        """Assign the sub-game to its backend, then acknowledge that assignment."""
        try:
            return await gateway.negotiate(message)
        except BaseException as failure:
            raise outbound(failure) from None

    @server.tool
    async def receive_turn(message: KitJson) -> dict[str, bool]:
        """Route one half-turn to the backend playing the live sub-game."""
        try:
            return await gateway.receive_turn(message)
        except BaseException as failure:
            raise outbound(failure) from None

    @server.tool
    async def submit_audit(payload: KitJson) -> dict[str, bool]:
        """Route a disclosure to the backend whose sub-game is settling."""
        try:
            return await gateway.submit_audit(payload)
        except BaseException as failure:
            raise outbound(failure) from None

    @server.tool
    async def receive_control(message: KitJson) -> dict[str, bool]:
        """Route a status signal. It moves no cursor and settles nothing."""
        try:
            return await gateway.receive_control(message)
        except BaseException as failure:
            raise outbound(failure) from None

    return server


def build_gateway_admin(gateway: KitGroupGateway, name: str = "mars777-group-admin") -> FastMCP:
    """The loopback-only surface a role backend uses to report its settlement."""
    server: FastMCP = FastMCP(name, strict_input_validation=True)

    @server.tool
    async def sub_game_settled(sub_game: int) -> dict[str, bool]:
        """The backend that played *sub_game* owes nothing more for it."""
        try:
            gateway.settle(sub_game)
        except BaseException as failure:
            raise outbound(failure) from None
        return KIT_OK

    return server
