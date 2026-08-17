"""Booting two real agents and letting their own drivers play sub-game one.

Every earlier lifecycle proof handed the turns their actions and the sub-game
its outcome. This one hands over neither: each side's own `BaselineStrategy`
picks its move from an `Observation` built out of its own truth, and the end
event comes back from `domain.terminal` after the real locked survival
threshold. The harness starts two servers and wires two drivers; it decides
nothing about the game.

The terminal is `SURVIVAL` on purpose rather than by luck. The Stage-6B police
baseline has no belief, so it places no barrier and declares no capture - which
leaves exactly one source-defined way for this sub-game to end, and the tests
below let it run all the way there on source-compliant parameters.

**What is proved here is gameplay, not the series lifecycle.** `SubGameDriver`
owns the observation, the strategy call, the commit/acknowledge/reveal cadence,
the one-time truth adoption and the terminal derivation. Everything this module
adds around it is existing bookkeeping: `close_turn` carries a finished round's
peer evidence into the audit and takes neither an action nor an outcome, and the
loop continues only while **the drivers'** own `settled()` says the sub-game has
not ended. Composing that bookkeeping into `SeriesRuntime`, the exact-six
lifecycle and a CLI/two-process boot is Stage 6C-C.
"""

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

import boot_builders as build
import r7_builders as r7
from r16_builders import GROUP_A, GROUP_B

from mars777_police.app.config_rules import hints_of
from mars777_police.app.sealed_record_values import ActorRole
from mars777_police.app.sub_game_driver import SubGameDriver
from mars777_police.app.turn_service import LocalTurnService
from mars777_police.domain.barriers import BarrierQuota
from mars777_police.domain.terminal import Outcome, TurnLimits
from mars777_police.domain.truth import LocalTruth
from mars777_police.series_runtime import SeriesRuntime

SIDES = ((ActorRole.POLICE, GROUP_A), (ActorRole.THIEF, GROUP_B))
LIMITS = TurnLimits(max_moves=35, survival_threshold=35)
QUOTA = BarrierQuota(max_barriers=14)


def pair_for(root: Path) -> tuple[SeriesRuntime, SeriesRuntime]:
    """Two independently composed agents, each with its own artifact root."""
    port_a, port_b = build.pair_urls()
    agent_a, agent_b = r7.agents(port_a, port_b)
    roots = (root / "police", root / "thief")
    a, b = (
        r7.series_for(agent, r7.store_for(where))
        for agent, where in zip((agent_a, agent_b), roots, strict=True)
    )
    return a, b


@asynccontextmanager
async def started(a: SeriesRuntime, b: SeriesRuntime) -> AsyncIterator[None]:
    """Serve both, then let each connect and exchange its own Step-0."""
    await a.agent.serve()
    await b.agent.serve()
    try:
        await a.start()
        await b.start()
        yield
    finally:
        await a.agent.stop()
        await b.agent.stop()


def driver_for(series: SeriesRuntime, role: ActorRole) -> SubGameDriver:
    """The production driver for one side of sub-game one. No action, no outcome."""
    composition = series.composition
    return SubGameDriver(
        strategy=composition.strategy,
        runner=composition.peer_runner,
        context=composition.runtime_context,
        role=role,
        turns=LocalTurnService(limits=LIMITS, quota=QUOTA),
        config_sha256=r7.DIGEST,
        hints=hints_of(r7.CONFIG, role),
        sub_game=1,
        truth=LocalTruth(board=r7.board(), own_position=r7.POSITIONS[role]),
        deadline=30.0,
    )


async def _open_g01(a: SeriesRuntime, b: SeriesRuntime) -> None:
    """The real pregame for sub-game one: config, lock, evidence and audit."""
    for series, group in zip((a, b), (GROUP_A, GROUP_B), strict=True):
        r7.open_config(series, group, 1)
    r7.lock_round(a, b)
    for series in (a, b):
        series.lock_config(r7.CONFIG)
    for series, (role, _), peer in zip(
        (a, b), SIDES, ((ActorRole.THIEF, GROUP_B), (ActorRole.POLICE, GROUP_A)), strict=True
    ):
        series.open_sub_game(r7.evidence_for(role, 1), r7.audit_for(peer[0], peer[1], 1))


async def play(a: SeriesRuntime, b: SeriesRuntime) -> tuple[Outcome, Outcome, int]:
    """Drive one autonomous sub-game and report what each driver decided."""
    drivers = [driver_for(a, ActorRole.POLICE), driver_for(b, ActorRole.THIEF)]
    for driver in drivers:
        driver.open()
    rounds = 0
    while all(driver.settled() is None for driver in drivers):
        witnessed = [series.composition.runtime_context.current_turn() for series in (a, b)]
        await asyncio.gather(*(driver.play_round() for driver in drivers))
        for series, turn in zip((a, b), witnessed, strict=True):
            series.close_turn(turn)
        rounds += 1
    settled = [driver.settled() for driver in drivers]
    assert settled[0] is not None and settled[1] is not None
    return settled[0], settled[1], rounds


async def _finish(a: SeriesRuntime, b: SeriesRuntime) -> None:
    """Both nonce batches, then both disclosures - the existing audit stack."""
    for series in (a, b):
        await series.composition.peer_runner.send_final_nonce_reveal()
    for series in (a, b):
        await series.composition.peer_runner.send_audit_disclosure()


async def autonomous(a: SeriesRuntime, b: SeriesRuntime) -> tuple[Outcome, int]:
    """One whole natural sub-game, from Step-0 to a stored official log."""
    async with started(a, b):
        for series in (a, b):
            series.record_declaration()
        await _open_g01(a, b)
        police, thief, rounds = await play(a, b)
        assert police is thief
        await _finish(a, b)
        for series in (a, b):
            series.tokens.charge(1, 0)
            series.close_sub_game(police)
        return police, rounds
