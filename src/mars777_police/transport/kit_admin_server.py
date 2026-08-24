"""The private admin surface a role backend reports its own series facts on.

Split from the public gateway server under guideline 3.2, and the split is the
distinction that matters most here: everything in this file is loopback-only and
must never appear on the route an opponent can reach. Keeping it in its own
module makes "is this tool public?" a question about which file it lives in.

Four calls, and each exists because a two-process group has one fact that
neither process holds alone: which sub-game is finished, which rows it settled
as, which official documents it produced, and which whole-series digest it
agreed with the peer.
"""

import asyncio
from collections.abc import Awaitable, Callable

from fastmcp import FastMCP

from ..app.kit_messages import KitRole
from .kit_envelopes import KIT_OK, KitJson
from .kit_gateway import KitGroupGateway
from .kit_series_writeout import write_series
from .wire_errors import outbound


def _await_within(deadline: float) -> "Callable[[object], Awaitable[None]]":
    """Wait on a milestone the peer's inbound request sets, within the deadline."""

    async def wait(arrived: object) -> None:
        assert isinstance(arrived, asyncio.Event)
        await asyncio.wait_for(arrived.wait(), deadline)

    return wait


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
    async def contribute_entry(
        sub_game: int, role: str, github_commit: str, tokens: int
    ) -> dict[str, bool]:
        """Hand the group this backend's own entry for a sub-game it played."""
        try:
            gateway.contribute_entry(sub_game, KitRole(role), github_commit, tokens)
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
    async def agree_result() -> dict[str, bool]:
        """Run the group's one result agreement, after the series has settled.

        Called by the backend that owned the final sub-game, because that is the
        process that knows the settlement completed. The agreement itself is the
        gateway's: it is series-wide, and no backend holds a whole series.
        """
        try:
            if gateway.agreement is None:
                return {"ok": False}
            agreed = await gateway.agreement.settle(_await_within(gateway.deadline))
            if agreed:
                write_series(gateway)
            return {"ok": agreed}
        except BaseException as failure:
            raise outbound(failure) from None

    @server.tool
    async def series_settled(consensus_sha256: str) -> dict[str, bool]:
        """Report the digest this group agreed with the peer for the whole series."""
        try:
            gateway.series_settled(consensus_sha256)
        except BaseException as failure:
            raise outbound(failure) from None
        return KIT_OK

    @server.tool
    async def series_rows() -> list[KitJson]:
        """The group's six finished rows, for whichever backend settles the series."""
        try:
            return list(gateway.series_rows())
        except BaseException as failure:
            raise outbound(failure) from None

    return server
