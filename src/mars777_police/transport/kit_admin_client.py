"""The loopback call a role backend makes to report that a sub-game is settled.

Its own client rather than the peer one: this is not a peer, not a KIT message
and not part of any wire a partner sees. It is one private call on one private
surface, and giving it a separate owner keeps it impossible to send by accident
down the path that talks to an opponent.

Settlement is **signalled**, never inferred - a peer that is thinking and a
sub-game that has finished look identical from the outside, and guessing between
them is how a sub-game gets skipped.
"""

from contextlib import AsyncExitStack
from dataclasses import dataclass, field

from fastmcp import Client

SETTLED_TOOL = "sub_game_settled"
"""The one operation this client makes. There is no second admin call."""


@dataclass(slots=True)
class KitAdminClient:
    """One held session to the group gateway's loopback admin surface."""

    url: str
    _stack: AsyncExitStack | None = field(default=None)
    _client: Client | None = field(default=None)  # type: ignore[type-arg]

    async def __aenter__(self) -> "KitAdminClient":
        """Open the session the whole series reports over."""
        stack = AsyncExitStack()
        self._client = await stack.enter_async_context(Client(self.url))
        self._stack = stack
        return self

    async def __aexit__(self, kind: object, value: object, traceback: object) -> None:
        """Close it exactly once, whatever happened inside."""
        stack, self._stack, self._client = self._stack, None, None
        if stack is not None:
            await stack.aclose()

    async def settled(self, sub_game: int) -> None:
        """Report that *sub_game* owes nothing more, so routing may move on."""
        if self._client is None:
            raise RuntimeError("the admin session is not open")
        await self._client.call_tool(SETTLED_TOOL, {"sub_game": sub_game})
