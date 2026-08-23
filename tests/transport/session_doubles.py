"""Stand-ins for the two halves of a held session, shared by the hold tests.

A session double rather than a mock: it is a real async context with a real
identity, so the tests observe the same thing production does - which id is in
use before and after the peer disowns one.
"""

from mcp.shared.exceptions import McpError
from mcp.types import ErrorData

from mars777_police.transport.session_hold import SESSION_NOT_FOUND_CODE


def session_gone() -> McpError:
    """Exactly what the MCP client raises when a POST is answered with 404."""
    return McpError(ErrorData(code=SESSION_NOT_FOUND_CODE, message="Session terminated"))


class OpenedSession:
    """An async context with a stable identity, standing in for one session."""

    def __init__(self, identity: str = "session-0") -> None:
        self.identity = identity
        self.closed = False

    async def __aenter__(self) -> "OpenedSession":
        return self

    async def __aexit__(self, *_: object) -> None:
        self.closed = True

    @property
    def transport(self) -> "OpenedSession":
        """The hold reads the id through the transport, as FastMCP exposes it."""
        return self

    def get_session_id(self) -> str:
        return self.identity
