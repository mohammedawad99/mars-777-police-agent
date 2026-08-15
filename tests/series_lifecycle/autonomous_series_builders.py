"""Booting two real agents and letting their own series drivers play all six.

The harness starts two servers, hands each side one valid series configuration
as boot input, and calls `play_series()`. It decides nothing after that: no
action, no outcome, no round bookkeeping, no config round, no audit call and no
result cadence - all of those are production owners now.

A configuration handed in as boot input is not a gameplay decision. What 6C-C1
proves is autonomous *execution* of the series and its negotiation protocol, not
an intelligent autonomous choice of negotiable values; the same locked values
are proposed for every sub-game except its own `sub_game` identity.
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

import boot_builders as build
import r7_builders as r7
from r16_builders import GROUP_A, GROUP_B

from mars777_police.app.audit_runtime import AuditRuntime
from mars777_police.app.outbound_evidence_runtime import OutboundEvidenceRuntime
from mars777_police.app.sealed_record_values import ActorRole
from mars777_police.series_driver import SeriesDriver
from mars777_police.series_runtime import SeriesRuntime

SIDES = ((ActorRole.POLICE, GROUP_A), (ActorRole.THIEF, GROUP_B))
PEERS = {ActorRole.POLICE: (ActorRole.THIEF, GROUP_B), ActorRole.THIEF: (ActorRole.POLICE, GROUP_A)}


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


def runtimes_for(role: ActorRole) -> object:
    """How this side builds one sub-game's producer and verifier."""
    peer_role, peer_group = PEERS[role]

    def build_them(sub_game: int) -> tuple[OutboundEvidenceRuntime, AuditRuntime]:
        return r7.evidence_for(role, sub_game), r7.audit_for(peer_role, peer_group, sub_game)

    return build_them


def driver_for(series: SeriesRuntime, role: ActorRole) -> SeriesDriver:
    """The production series owner for one side. No action, no outcome."""
    return SeriesDriver(
        series=series,
        strategy=series.composition.strategy,
        role=role,
        config=r7.CONFIG,
        runtimes=runtimes_for(role),  # type: ignore[arg-type]
        deadline=60.0,
    )


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
