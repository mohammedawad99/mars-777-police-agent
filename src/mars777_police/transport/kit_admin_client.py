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
from typing import Any

from fastmcp import Client

SETTLED_TOOL = "sub_game_settled"
CONTRIBUTE_TOOL = "contribute_row"
ROWS_TOOL = "series_rows"
ARTIFACT_TOOL = "contribute_artifact"
"""The three private operations. None of them is a KIT message or reaches a peer."""


@dataclass(slots=True)
class KitAdminClient:
    """One held session to the group gateway's loopback admin surface."""

    url: str
    _stack: AsyncExitStack | None = field(default=None)
    _client: "Client[Any] | None" = field(default=None)

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
        await self._open().call_tool(SETTLED_TOOL, {"sub_game": sub_game})

    async def contribute(self, row: dict[str, Any]) -> None:
        """Hand the group one finished row, so the series can settle as a whole.

        Each backend plays three of the six sub-games, so neither holds the
        series a settlement digest covers; this is how the two halves meet while
        both processes are still alive.
        """
        await self._open().call_tool(CONTRIBUTE_TOOL, {"row": row})

    async def contribute_artifact(self, kind: str, sub_game: int, document: dict[str, Any]) -> None:
        """Hand the group one official per-sub-game document it must write out.

        Same reason the rows travel this way: a two-process group owes one set
        of fourteen files and neither process holds all twelve halves.
        """
        await self._open().call_tool(
            ARTIFACT_TOOL, {"kind": kind, "sub_game": sub_game, "document": document}
        )

    async def series_rows(self) -> list[dict[str, Any]]:
        """The group's six finished rows, for whichever backend settles the series."""
        result = await self._open().call_tool(ROWS_TOOL, {})
        rows = result.data
        if not isinstance(rows, list):
            raise RuntimeError(f"the group returned {type(rows).__name__}, not a list of rows")
        return [dict(row) for row in rows]

    def _open(self) -> "Client[Any]":
        """The held session, or a refusal that names the real mistake."""
        if self._client is None:
            raise RuntimeError("the admin session is not open")
        return self._client
