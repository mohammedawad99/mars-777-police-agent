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

from fastmcp import Context, FastMCP

from ..app.protocol_errors import AuthFailureError, LocalDefectError, MalformedMessageError
from ..app.series_result_authority import authenticated_sender, raw_payload
from .codec_auth import decode_auth
from .codec_final import decode_result_agreement
from .kit_admin_server import build_gateway_admin as build_gateway_admin
from .kit_control_envelope import KitResultAgreementMessage, parse_kit_control
from .kit_envelopes import KIT_OK, KitJson
from .kit_gateway import KitGroupGateway
from .negotiate_arguments import Step0Handler, step0_arguments
from .session_state import inbound
from .wire_errors import outbound

GATEWAY_TOOLS = ("negotiate", "receive_turn", "submit_audit", "receive_control")
"""The public surface, identical to a backend's. The router is invisible."""

ADMIN_TOOLS = (
    "sub_game_settled",
    "contribute_row",
    "contribute_entry",
    "contribute_artifact",
    "official_artifact",
    "agree_result",
    "series_settled",
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
    ) -> KitJson:
        """Accept a sub-game greeting or the one authenticated Step-0.

        The greeting answer carries our `group_id` beside the pinned `ok`, so a
        peer can derive the same `game_id` we do. Step-0 keeps the bare object.
        """
        try:
            exchange = step0_arguments(message, request, kind, payload)
            if exchange is not None:
                if step0 is None:
                    raise LocalDefectError(
                        "this gateway was given no Step-0 receiver, so an authenticated"
                        " Step-0 has nowhere to go; a counted series must not proceed",
                    )
                await step0(exchange)
                return {**KIT_OK}
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
    async def receive_control(message: KitJson, session: Context) -> dict[str, bool] | str:
        """Route a status signal, or answer the group's one result agreement.

        The status form still routes to a backend and still answers `{"ok": True}`.
        The result agreement is a **series-wide** fact no backend holds, so it is
        answered here, from the group's single agreement authority, and returns
        `result_sha256` as 64 lowercase hex. The sender must be the peer this
        session authenticated: `require_peer` refuses before any state is read.
        """
        bound = await inbound(session)
        try:
            control = parse_kit_control(message)
            if isinstance(control, KitResultAgreementMessage):
                if gateway.agreement is None:
                    raise LocalDefectError(
                        "this gateway owns no result agreement, so a counted result"
                        " cannot be agreed here; the run is not a counted one",
                    )
                agreed = decode_result_agreement(control.payload)
                if bound.peer is None and gateway.requests is None:
                    raise AuthFailureError(
                        "this run provisioned no request authenticator, so a result"
                        " agreement on an unauthenticated session cannot be verified",
                    )
                sender = authenticated_sender(
                    bound.peer,
                    raw_payload(message),
                    None if control.auth is None else decode_auth(control.auth),
                    gateway.declaration,
                    gateway.group_id,
                    gateway.requests,  # type: ignore[arg-type]
                )
                digest = await gateway.agreement.accept(agreed, sender, gateway.deadline)
                return digest.value
            return await gateway.receive_control(message)
        except BaseException as failure:
            raise outbound(failure) from None

    return server
