"""The FastMCP client adapter: the concrete outbound peer transport.

Owns the endpoint, the tool invocation, the per-call timeout, response decoding
and framework-error translation - and **no** gameplay state: no cadence, no
commitment verification, no legality.

**Timeouts come from the locked config**: `for_locked_config` reads
`response_timeout_sec` off the agreed `NegotiatedConfig` through `TimeoutPolicy`,
and `for_bootstrap` uses the negotiation window. No number appears here.

Every response is decoded **strictly**: a completing operation refuses a value,
`reveal` requires an exact `TurnOutcome`, and a digest must be well formed.

**One session per peer lifecycle, not one per operation.** Entering this client
as an async context holds one FastMCP Streamable-HTTP session and runs every
`call_tool` inside it. That is measured: over a real public tunnel, 30 operations
each opening their own session failed from the twenty-first onward, while the
same 30 in one held session all succeeded. Outside one, each call opens its own.

**A dead session is not silently replaced.** It surfaces as `E-TRANSPORT` and is
never replayed: whether a commitment reached the peer is unknowable here.
"""

from contextlib import AsyncExitStack
from typing import Any

from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport
from fastmcp.exceptions import ToolError
from pydantic import BaseModel, ValidationError

from ..app.capture_values import TurnOutcome
from ..app.peer_supervision import TimeoutPolicy
from ..app.protocol_errors import MalformedMessageError
from ..app.protocol_values import InvalidDigestError, Sha256Digest
from ..domain.negotiated_config import NegotiatedConfig
from .codec_turn import decode_outcome
from .wire_errors import TransportFailureError, inbound
from .wire_turn import TurnOutcomeWire


def wire_json(model: BaseModel) -> dict[str, object]:
    """Render a DTO for the wire, **omitting** every absent member.

    `exclude_none=True` is the contract, not a convenience: a member that is
    absent must not arrive as `null`. That is what keeps a CPU-only
    participant's `vram_gb` out of the authenticated Step-0 core entirely.
    """
    return model.model_dump(mode="json", exclude_none=True)


def envelope(kind: str, payload: BaseModel | dict[str, object]) -> dict[str, object]:
    """Build the one frozen argument: `request = {kind, payload}`."""
    body = wire_json(payload) if isinstance(payload, BaseModel) else payload
    return {"request": {"kind": kind, "payload": body}}


class PeerClient:
    """One peer endpoint, one connection lifecycle, no shared global state."""

    def __init__(self, url: str, timeout: float) -> None:
        self._url = url
        self._timeout = timeout
        self._session: Client[StreamableHttpTransport] | None = None
        self._stack: AsyncExitStack | None = None

    @classmethod
    def for_locked_config(
        cls, url: str, config: NegotiatedConfig, policy: TimeoutPolicy
    ) -> "PeerClient":
        """Bind the per-call deadline to the **agreed** `response_timeout_sec`."""
        return cls(url, policy.for_config(config))

    @classmethod
    def for_bootstrap(cls, url: str, policy: TimeoutPolicy) -> "PeerClient":
        """Bind pre-lock calls to the negotiation window the state owns."""
        return cls(url, policy.bootstrap())

    @property
    def timeout(self) -> float:
        """The deadline every call on this client carries."""
        return self._timeout

    @property
    def url(self) -> str:
        """The peer's stable group-level ingress."""
        return self._url

    def _client(self) -> Client[StreamableHttpTransport]:
        return Client(StreamableHttpTransport(self._url), timeout=self._timeout)

    async def __aenter__(self) -> "PeerClient":
        """Hold one session open for every call made inside this context."""
        stack = AsyncExitStack()
        try:
            self._session = await stack.enter_async_context(self._client())
        except Exception as failure:
            await stack.aclose()
            raise TransportFailureError(TransportFailureError.error_id) from failure
        self._stack = stack
        return self

    async def __aexit__(self, kind: object, value: object, traceback: object) -> None:
        """Close the held session exactly once, whatever happened inside."""
        stack, self._stack, self._session = self._stack, None, None
        if stack is not None:
            await stack.aclose()

    async def call(self, tool: str, kind: str, payload: BaseModel | dict[str, object]) -> Any:
        """Invoke *tool* with the frozen envelope and return its raw result."""
        request = envelope(kind, payload)
        try:
            if self._session is not None:
                result = await self._session.call_tool(tool, request, timeout=self._timeout)
            else:
                async with self._client() as client:
                    result = await client.call_tool(tool, request, timeout=self._timeout)
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
