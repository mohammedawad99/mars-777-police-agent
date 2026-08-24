"""The FastMCP client adapter: the concrete outbound peer transport.

Owns the endpoint, the tool invocation, the per-call timeout, response decoding
and framework-error translation - and **no** gameplay state: no cadence, no
commitment verification, no legality.

**Timeouts come from the locked config**, through the `PeerDeadline` this
client is composed with: the negotiation window until a lock is verified, the
agreed `response_timeout_sec` afterwards. No number appears here, and none is
stored - the deadline is read per call, so a lock verified after this object
was built still governs it.

Every response is decoded **strictly**: a completing operation refuses a value,
`reveal` requires an exact `TurnOutcome`, and a digest must be well formed.

**One session per peer lifecycle, not one per operation**, and a dead one is
never silently replaced: `E-TRANSPORT` stays terminal because whether a
commitment reached the peer is unknowable here. `session_hold` owns both rules
and the one case - a peer that disowns our session id - where re-establishing is
lifecycle rather than replay. Outside a held session each call opens its own.

**The wire shape belongs to the transport profile**, not here: `call_arguments`.
"""

from typing import Any

from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport
from fastmcp.exceptions import ToolError
from pydantic import BaseModel, ValidationError

from ..app.capture_values import TurnOutcome
from ..app.peer_supervision import PeerDeadline
from ..app.protocol_errors import MalformedMessageError
from ..app.protocol_values import InvalidDigestError, Sha256Digest
from .call_arguments import arguments_for
from .call_arguments import wire_json as wire_json
from .codec_turn import decode_outcome
from .session_deadline import session_transport
from .session_hold import HeldSession
from .transport_profiles import TransportEnvelopeProfile as Envelopes
from .wire_errors import TransportFailureError, inbound
from .wire_turn import TurnOutcomeWire

STRICT = Envelopes.STRICT_PROJECT  # the default: every existing flow keeps its own surface


class PeerClient:
    """One peer endpoint, one connection lifecycle, no shared global state."""

    def __init__(self, url: str, deadline: PeerDeadline, profile: Envelopes = STRICT) -> None:
        self._url = url
        self._deadline = deadline
        self._profile = profile
        self._hold = HeldSession(self._client)

    @property
    def profile(self) -> Envelopes:
        """The one wire this client speaks, fixed when it was constructed."""
        return self._profile

    @property
    def deadline(self) -> PeerDeadline:
        """The authority this client and its held session both answer to."""
        return self._deadline

    @property
    def timeout(self) -> float:
        """The deadline a call made now would carry.

        Read through the authority rather than stored, so the value both peers
        locked governs every request from the moment they locked it.
        """
        return self._deadline.seconds()

    @property
    def session_id(self) -> str | None:
        """The outbound MCP session id now in use, or None outside a session."""
        return self._hold.session_id

    @property
    def url(self) -> str:
        """The peer's stable group-level ingress."""
        return self._url

    def _client(self) -> Client[StreamableHttpTransport]:
        """One session whose read budget follows the lock it was opened before."""
        return Client(session_transport(self._url, self._deadline), timeout=self.timeout)

    async def __aenter__(self) -> "PeerClient":
        """Hold one session for this context; eager, so it proves the peer is up."""
        try:
            await self._hold.open()
        except Exception as failure:
            raise TransportFailureError(TransportFailureError.error_id) from failure
        return self

    async def __aexit__(self, kind: object, value: object, traceback: object) -> None:
        """Close the held session exactly once, whatever happened inside."""
        await self._hold.close()

    async def call(self, tool: str, kind: str, payload: BaseModel | dict[str, object]) -> Any:
        """Invoke *tool* with the frozen envelope and return its raw result."""
        return await self.invoke(tool, arguments_for(kind, payload, self._profile))

    async def invoke(self, tool: str, request: dict[str, object]) -> Any:
        """Send one already-built argument object, inside the held session."""

        async def send(session: Client[StreamableHttpTransport]) -> Any:
            return await session.call_tool(tool, request, timeout=self.timeout)

        try:
            if self._hold.held:
                result = await self._hold.run(send)
            else:
                async with self._client() as client:
                    result = await send(client)
        except ToolError as failure:
            raise inbound(str(failure)) from None
        except Exception as failure:
            raise TransportFailureError(TransportFailureError.error_id) from failure
        return result.data

    async def complete(self, tool: str, kind: str, payload: BaseModel | dict[str, object]) -> None:
        """Call an operation that must complete carrying no semantic value."""
        data = await self.call(tool, kind, payload)
        if data is not None:
            raise MalformedMessageError(MalformedMessageError.error_id)

    async def outcome(self, payload: BaseModel) -> TurnOutcome:
        """Call `reveal` and require an exact `TurnOutcome` result.

        The framework returns structured output as a mapping or as a model it
        rebuilt, so both go through the one wire model rather than being trusted.
        """
        data = await self.call("receive_turn", "reveal", payload)
        try:
            return decode_outcome(TurnOutcomeWire.model_validate(data, from_attributes=True))
        except ValidationError:
            raise MalformedMessageError(MalformedMessageError.error_id) from None

    async def digest(self, payload: BaseModel) -> Sha256Digest:
        """Call `receive_control` and require a well-formed `Sha256Digest`."""
        data = await self.call("receive_control", "result_agreement", payload)
        if type(data) is not str:
            raise MalformedMessageError(MalformedMessageError.error_id)
        try:
            return Sha256Digest(data)
        except InvalidDigestError:
            raise MalformedMessageError(MalformedMessageError.error_id) from None
