"""Two real agents, six real sub-games, fourteen official files.

This is the lifecycle proof, not a strategy proof: the tests choose the actions
and the terminal outcomes, and everything else - digests, nonces, verdicts,
scores, totals, filenames and bytes - is produced by production code.
"""

import asyncio
from collections.abc import AsyncIterator, Iterator
from contextlib import asynccontextmanager
from pathlib import Path

import boot_builders as build
import pytest
import r7_builders as r7
from r16_builders import GROUP_A, GROUP_B

from mars777_police.app.sealed_record_values import ActorRole
from mars777_police.app.turn_cursor import TurnCursor
from mars777_police.domain.terminal import Outcome
from mars777_police.series_runtime import SeriesRuntime

SIDES = ((ActorRole.POLICE, GROUP_A), (ActorRole.THIEF, GROUP_B))


def pair_for(root: Path) -> tuple[SeriesRuntime, SeriesRuntime]:
    """Two series owners over two real agents, each with its own artifact root."""
    port_a, port_b = build.pair_urls()
    agent_a, agent_b = r7.agents(port_a, port_b)
    roots = (root / "police", root / "thief")
    a, b = (
        r7.series_for(agent, r7.store_for(where))
        for agent, where in zip((agent_a, agent_b), roots, strict=True)
    )
    return a, b


@pytest.fixture
def pair(tmp_path: Path) -> Iterator[tuple[SeriesRuntime, SeriesRuntime]]:
    """A fresh pair for one test."""
    yield pair_for(tmp_path)


@asynccontextmanager
async def started(a: SeriesRuntime, b: SeriesRuntime) -> AsyncIterator[None]:
    """Serve both agents, then let each series connect and exchange Step-0."""
    await a.agent.serve()
    await b.agent.serve()
    try:
        await a.start()
        await b.start()
        for series in (a, b):
            series.record_declaration()
        yield
    finally:
        await a.agent.stop()
        await b.agent.stop()


async def play_sub_game(a: SeriesRuntime, b: SeriesRuntime, sub_game: int, tamper: bool) -> None:
    """One whole sub-game: config lock, two real turns, and the final audit."""
    for series, group in zip((a, b), (GROUP_A, GROUP_B), strict=True):
        r7.open_config(series, group, sub_game)
    r7.lock_round(a, b)
    for series in (a, b):
        series.lock_config(r7.CONFIG)
    for series, (role, _), peer in zip(
        (a, b), SIDES, ((ActorRole.THIEF, GROUP_B), (ActorRole.POLICE, GROUP_A)), strict=True
    ):
        series.open_sub_game(
            r7.evidence_for(role, sub_game), r7.audit_for(peer[0], peer[1], sub_game)
        )
    for mover, waiter, role, step in ((a, b, ActorRole.POLICE, 1), (b, a, ActorRole.THIEF, 2)):
        cursor = TurnCursor(sub_game, step)
        for series, side in ((mover, role), (waiter, _other(role))):
            series.composition.runtime_context.bind_turn(r7.turn_for(side, cursor))
        assert (await r7.one_turn(mover, waiter, role, cursor)).accepted is True
        for series in (mover, waiter):
            series.close_turn(series.composition.runtime_context.current_turn())
    await _final_audit(a, b, tamper)


def _other(role: ActorRole) -> ActorRole:
    return ActorRole.THIEF if role is ActorRole.POLICE else ActorRole.POLICE


async def _final_audit(a: SeriesRuntime, b: SeriesRuntime, tamper: bool) -> None:
    """Both nonce batches, then both disclosures - one of them optionally doctored."""
    for series in (a, b):
        await series.composition.peer_runner.send_final_nonce_reveal()
    document = a.composition.runtime_context.current_evidence().audit_disclosure()
    if tamper:
        entries = document["entries"]
        assert isinstance(entries, list)
        entries[0]["hint"] = "a hint we never sent"
    await a.composition.peer_transport.send_audit_disclosure(document)
    await b.composition.peer_runner.send_audit_disclosure()


async def run_series(
    a: SeriesRuntime, b: SeriesRuntime, outcomes: tuple[Outcome, ...], tamper: bool = False
) -> None:
    """Play the whole six-sub-game series and record each terminal outcome."""
    async with started(a, b):
        for index, outcome in enumerate(outcomes, start=1):
            await play_sub_game(a, b, index, tamper and index == 1)
            for series in (a, b):
                series.tokens.charge(index, 120)
                series.close_sub_game(outcome)
        if not tamper:
            await _agree(a, b)


async def _agree(a: SeriesRuntime, b: SeriesRuntime) -> None:
    """Build both result owners late, then drive the real two-direction cadence."""
    for series in (a, b):
        series.build_result()
    await b.composition.peer_runner.open_result_agreement()
    timestamp = a.composition.runtime_context.current_result().timestamp
    assert timestamp is not None
    await a.composition.peer_runner.respond_to_result(timestamp)


def names(root: Path) -> list[str]:
    return sorted(path.name for path in root.iterdir())


def test_a_completed_series_writes_exactly_the_fourteen_official_files(pair: tuple) -> None:
    a, b = pair
    asyncio.run(run_series(a, b, (Outcome.CAPTURE,) * 6))
    for series in (a, b):
        stored = series.persist_result()
        root = Path(stored.path).parent
        expected = [f"config_{r7.GAME_ID}_g0{n}.json" for n in range(1, 7)]
        expected += [f"declaration_{r7.GAME_ID}.json"]
        expected += [f"log_{r7.GAME_ID}_g0{n}.json" for n in range(1, 7)]
        expected += [f"result_{r7.GAME_ID}.json"]
        assert names(root) == sorted(expected)
        assert len(names(root)) == 14
