"""The FastMCP client adapter: the concrete outbound peer transport.

Owns the target endpoint, the tool invocation, the per-call timeout, response
decoding and framework-error translation. It owns **no** gameplay state: it
decides no cadence, verifies no commitment and never re-derives legality.

**Timeouts come from the locked config**, and the link is typed rather than
trusted: `for_locked_config` reads `response_timeout_sec` off the agreed
`NegotiatedConfig` through the application's `TimeoutPolicy`, and `for_bootstrap`
uses the negotiation window the state already owns. 30 is that member's
Appendix-F baseline, not a constant, and no number appears in this module.

Every response is decoded **strictly**: an operation that must complete with no
semantic value refuses one, `reveal` requires an exact `bool` rather than `0`,
`1` or `"true"`, and the digest must be a well-formed `Sha256Digest`.

**One session per peer lifecycle, not one per operation.** Entering this client
as an async context holds a single FastMCP Streamable-HTTP session open and runs
every `call_tool` inside it. That is measured, not preferred: over a real public
tunnel, 30 operations each opening their own session failed from the twenty-first
onward and left the route unreachable, while the same 30 inside one held session
all succeeded - in both experiment orders. Outside a held session each call still
opens its own, so a caller managing no lifecycle keeps the original behaviour.

**A dead session is not silently replaced.** The failure surfaces as
`E-TRANSPORT` and the operation is never replayed: whether a commitment reached
the peer is not knowable from here, so reconnection and semantic retry stay
separate decisions owned by the frozen retry policy.
"""

from contextlib import AsyncExitStack
from typing import Any

from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport
from fastmcp.exceptions import ToolError
from pydantic import BaseModel

from ..app.peer_supervision import TimeoutPolicy
from ..app.protocol_errors import MalformedMessageError
from ..app.protocol_values import InvalidDigestError, Sha256Digest
from ..domain.negotiated_config import NegotiatedConfig
from .wire_errors import TransportFailureError, inbound


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

    async def legality(self, payload: BaseModel) -> bool:
        """Call `reveal` and require an exact `bool` game-legality result."""
        data = await self.call("receive_turn", "reveal", payload)
        if type(data) is not bool:
            raise MalformedMessageError(MalformedMessageError.error_id)
        return data

    async def digest(self, payload: BaseModel) -> Sha256Digest:
        """Call `receive_control` and require a well-formed `Sha256Digest`."""
        data = await self.call("receive_control", "result_agreement", payload)
        if type(data) is not str:
            raise MalformedMessageError(MalformedMessageError.error_id)
        try:
            return Sha256Digest(data)
        except InvalidDigestError:
            raise MalformedMessageError(MalformedMessageError.error_id) from None
