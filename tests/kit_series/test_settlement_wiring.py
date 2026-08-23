"""The private wiring a two-process group settles through, exercised end to end.

Each half is small; together they are the difference between a series that
settles and one that is scored 0 for both groups. So each hop is checked here
rather than assumed to work because the pieces either side of it do.
"""

import asyncio
from typing import Any

import pytest
from fastmcp import Client

from mars777_police.app.kit_backend_settlement import (
    BackendSettlement,
    row_of,
    unavailable,
    uncollected,
)
from mars777_police.app.kit_greeting import KitPairing
from mars777_police.app.kit_handoff import SeriesHandoff
from mars777_police.app.kit_messages import KitAuditReveal, KitResultClaim, KitRole
from mars777_police.app.kit_schedule import SUB_GAMES
from mars777_police.app.protocol_errors import LocalDefectError, StaleMessageError
from mars777_police.app.series_consensus import consensus_scope, consensus_sha256
from mars777_police.domain.terminal import Outcome
from mars777_police.transport.kit_admin_client import KitAdminClient
from mars777_police.transport.kit_gateway import KitGroupGateway
from mars777_police.transport.kit_gateway_server import build_gateway_admin

OURS, THEIRS = "MaRs-777", "sparring-s82kma9e"
GAME_ID = "MaRs-777-vs-sparring-s82kma9e"


def pairing() -> KitPairing:
    return KitPairing(GAME_ID, "uid0001", OURS, THEIRS, KitRole.THIEF, KitRole.POLICE, 6, True)


def rows() -> list[dict[str, Any]]:
    return [
        row_of(
            pairing(),
            n,
            KitRole.POLICE if n % 2 else KitRole.THIEF,
            Outcome.SURVIVAL if n % 2 else Outcome.CAPTURE,
        )
        for n in range(1, SUB_GAMES + 1)
    ]


def gateway() -> KitGroupGateway:
    return KitGroupGateway(handoff=SeriesHandoff(KitRole.POLICE), routes={}, deadline=1.0)


def test_the_group_collects_rows_and_hands_back_the_series() -> None:
    held = gateway()
    for row in rows():
        held.contribute(row)
    assert [row["sub_game_number"] for row in held.series_rows()] == [1, 2, 3, 4, 5, 6]


def test_the_group_refuses_to_hand_back_an_incomplete_series() -> None:
    held = gateway()
    held.contribute(rows()[0])
    with pytest.raises(StaleMessageError, match="cannot settle"):
        held.series_rows()


def test_the_two_private_calls_work_over_a_real_loopback_session() -> None:
    """The hop that had no port at all when a real series needed it."""
    held = gateway()

    async def run() -> list[dict[str, Any]]:
        async with Client(build_gateway_admin(held)) as session:
            for row in rows():
                await session.call_tool("contribute_row", {"row": row})
            answer = await session.call_tool("series_rows", {})
        return list(answer.data)

    assert [row["sub_game_number"] for row in asyncio.run(run())] == [1, 2, 3, 4, 5, 6]


def test_a_refused_row_is_reported_as_a_refusal_over_the_wire() -> None:
    held = gateway()

    async def run() -> None:
        async with Client(build_gateway_admin(held)) as session:
            await session.call_tool("contribute_row", {"row": {"sub_game_number": 1}})

    with pytest.raises(Exception, match="E-PROTO-STALE"):
        asyncio.run(run())


def test_an_incomplete_series_is_reported_as_a_refusal_over_the_wire() -> None:
    held = gateway()

    async def run() -> None:
        async with Client(build_gateway_admin(held)) as session:
            await session.call_tool("series_rows", {})

    with pytest.raises(Exception, match="E-PROTO-STALE"):
        asyncio.run(run())


def test_the_admin_client_carries_rows_both_ways() -> None:
    held = gateway()

    async def run() -> list[dict[str, Any]]:
        client = KitAdminClient(build_gateway_admin(held))  # type: ignore[arg-type]
        async with client:
            for row in rows():
                await client.contribute(row)
            return await client.series_rows()

    assert len(asyncio.run(run())) == SUB_GAMES


def test_the_admin_client_refuses_to_speak_before_it_is_open() -> None:
    """A named refusal rather than an `AttributeError` on a `None`."""
    client = KitAdminClient("http://127.0.0.1:1/mcp")
    for call in (client.settled(1), client.contribute({}), client.series_rows()):
        with pytest.raises(RuntimeError, match="not open"):
            asyncio.run(call)


def test_a_backend_with_no_group_cannot_contribute_or_read() -> None:
    """The defaults are refusals, so an unwired backend fails loudly in a test."""
    with pytest.raises(LocalDefectError, match="contribute its rows"):
        asyncio.run(uncollected({}))
    with pytest.raises(LocalDefectError, match="read the group's series"):
        asyncio.run(unavailable())


def test_a_series_the_group_could_not_assemble_settles_on_nothing() -> None:
    """Six played sub-games are evidence worth keeping; the settlement is not."""

    async def partial() -> tuple[dict[str, Any], ...]:
        return tuple(rows()[:3])

    async def unreachable(envelope: dict[str, Any]) -> None:  # pragma: no cover - never called
        raise AssertionError("a series that cannot be assembled must not be sent")

    settlement = BackendSettlement(series_rows=partial, window=1.0, retry=0.05)
    agreed = asyncio.run(settlement.settle(pairing(), KitRole.THIEF, unreachable, lambda: None))
    assert agreed is None
    assert settlement.agreed is None


def test_a_complete_series_is_settled_through_the_backend_wiring() -> None:
    sent: list[dict[str, Any]] = []
    digest = consensus_sha256(consensus_scope(GAME_ID, rows(), OURS, THEIRS))

    async def series() -> tuple[dict[str, Any], ...]:
        return tuple(rows())

    async def send(envelope: dict[str, Any]) -> bool:
        sent.append(envelope)
        return True

    settlement = BackendSettlement(series_rows=series, window=1.0, retry=0.05)
    theirs = KitAuditReveal(KitRole.POLICE, (), KitResultClaim.SERIES_CONSENSUS, digest)
    agreed = asyncio.run(settlement.settle(pairing(), KitRole.THIEF, send, lambda: theirs))
    assert agreed == digest
    assert sent[0]["consensus_sha"] == digest
    assert sent[0]["sender"] == "thief"
