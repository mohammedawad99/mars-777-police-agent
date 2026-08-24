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

from fastmcp import FastMCP

from .kit_envelopes import KIT_OK, KitJson
from .kit_gateway import KitGroupGateway
from .wire_errors import outbound


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
