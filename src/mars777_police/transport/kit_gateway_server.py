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

from ..app.protocol_errors import LocalDefectError, MalformedMessageError
from .kit_envelopes import KIT_OK, KitJson
from .kit_gateway import KitGroupGateway
from .negotiate_arguments import Step0Handler, step0_arguments
from .wire_errors import outbound

GATEWAY_TOOLS = ("negotiate", "receive_turn", "submit_audit", "receive_control")
"""The public surface, identical to a backend's. The router is invisible."""

ADMIN_TOOLS = (
    "sub_game_settled",
    "contribute_row",
    "contribute_artifact",
    "official_artifact",
    "series_rows",
)
"""The private surface, loopback only, and never part of the KIT contract.

Listed in registration order, which a test compares against the live server."""


def build_gateway_tools(
    gateway: KitGroupGateway,
    name: str = "mars777-group",
    step0: Step0Handler | None = None,
) -> FastMCP:
    """The group's one opponent-facing ingress for a whole alternating series.

    **`negotiate` carries two different conversations**, and the pairing agreed
    all three spellings they arrive in:

    * `message={...}` - the per-sub-game reference-v3 handshake, six times;
    * `kind="step0", payload={...}` - the **agreed cross-team** Step-0, once;
    * `request={"kind":"step0","payload":{...}}` - the same Step-0 in this
      project's own native envelope, retained so our own client is unchanged.

    The third exists because the frozen contract recorded
    `{"tool":"negotiate","kind":"step0"}` without ever saying whether `kind` and
    `payload` were top-level arguments or nested under `request`. Both teams
    implemented to the letter and to different shapes: a rehearsal Step-0 was
    rejected at input validation before authentication. The rule was never
    stated, so neither reading was wrong, and accepting both costs nothing.

    **Dispatch is on shape, never on a caller-supplied selector**, and Step-0 is
    routed to the counted receiver rather than to a backend: it is a
    once-per-series group-level fact, and the six sub-games are what the
    backends own.
    """
    server: FastMCP = FastMCP(name, strict_input_validation=True)

    @server.tool
    async def negotiate(
        message: KitJson | None = None,
        request: KitJson | None = None,
        kind: str | None = None,
        payload: KitJson | None = None,
    ) -> dict[str, bool]:
        """Accept a sub-game greeting or the one authenticated Step-0."""
        try:
            exchange = step0_arguments(message, request, kind, payload)
            if exchange is not None:
                if step0 is None:
                    raise LocalDefectError(
                        "this gateway was given no Step-0 receiver, so an authenticated"
                        " Step-0 has nowhere to go; a counted series must not proceed",
                    )
                await step0(exchange)
                return KIT_OK
            if message is None:
                raise MalformedMessageError(
                    "negotiate needs message={...} for a sub-game greeting, or"
                    ' kind="step0" with payload={...} for the series Step-0',
                )
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

    @server.tool
    async def contribute_row(row: KitJson) -> dict[str, bool]:
        """Hand the group one finished row, so the series can be settled as a whole."""
        try:
            gateway.contribute(row)
        except BaseException as failure:
            raise outbound(failure) from None
        return KIT_OK

    @server.tool
    async def contribute_artifact(kind: str, sub_game: int, document: KitJson) -> dict[str, bool]:
        """Hand the group one official per-sub-game document it must write out."""
        try:
            gateway.contribute_artifact(kind, sub_game, document)
        except BaseException as failure:
            raise outbound(failure) from None
        return KIT_OK

    @server.tool
    async def official_artifact(kind: str, sub_game: int) -> KitJson | None:
        """One collected document, or `None` where none has been contributed."""
        try:
            return gateway.official_artifact(kind, sub_game)
        except BaseException as failure:
            raise outbound(failure) from None

    @server.tool
    async def series_rows() -> list[KitJson]:
        """The group's six finished rows, for whichever backend settles the series."""
        try:
            return list(gateway.series_rows())
        except BaseException as failure:
            raise outbound(failure) from None

    return server
