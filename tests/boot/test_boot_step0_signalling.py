"""When Step-0 is signalled, and what a signal without state would mean.

The peer's Step-0 had no awaitable moment at all until Stage 6C-C2 gave it one,
and the defect that hid behind that is the reason these exist: a signal must
follow the state it announces, never precede it, and one that arrived before we
were listening must not be missed.
"""

import asyncio
from pathlib import Path

import boot_builders as build
import composed_builders as compose
import pytest
from r16_builders import GROUP_A, GROUP_B
from test_autonomous_boot import closed_port, pair

from mars777_police.agent_runtime import AgentRuntime
from mars777_police.app.protocol_errors import (
    LocalDefectError,
)
from mars777_police.app.sealed_record_values import ActorRole

HOST = build.HOST


def test_step0_is_signalled_only_after_the_state_is_installed(tmp_path: Path) -> None:
    """The event reports a fact that is already true; it is never the fact."""
    a, b = pair()

    async def run() -> None:
        await a.serve()
        await b.serve()
        try:
            assert not a.composition.pregame.milestones.step0_seen.is_set()
            assert a.composition.pregame.peer is None
            await b.connect()
            await b.composition.peer_runner.send_step0(b.composition.identity.declaration)
            await asyncio.wait_for(a.composition.pregame.milestones.step0_seen.wait(), 10.0)
            assert a.composition.pregame.peer == GROUP_B
            assert a.composition.pregame.declaration.teams.group_b is not None
        finally:
            await a.stop()
            await b.stop()

    asyncio.run(run())


def test_a_step0_that_arrived_first_is_not_missed(tmp_path: Path) -> None:
    """`asyncio.Event` latches, so boot may start waiting after the arrival."""
    a, b = pair()

    async def run() -> None:
        await a.serve()
        await b.serve()
        try:
            await b.connect()
            await b.composition.peer_runner.send_step0(b.composition.identity.declaration)
            await asyncio.wait_for(a.composition.pregame.milestones.step0_seen.wait(), 10.0)
            await asyncio.wait_for(a.composition.pregame.milestones.step0_seen.wait(), 0.1)
        finally:
            await a.stop()
            await b.stop()

    asyncio.run(run())


def test_a_signalled_step0_without_a_peer_is_refused(tmp_path: Path) -> None:
    """The event says *when*; `pregame.peer` is the fact, and boot re-reads it."""
    import r7_builders as r7

    from mars777_police.autonomous_boot import AutonomousBoot
    from mars777_police.infra.settings import RuntimeSettings

    composition = build.agent(
        GROUP_A,
        ActorRole.POLICE,
        f"http://{HOST}:{closed_port()}/mcp",
    )
    runtime = AgentRuntime(composition, HOST, build.free_port())
    settings = compose.settings_for(ActorRole.POLICE, f"http://{HOST}:1/mcp", 8080)
    boot = AutonomousBoot(
        runtime,
        RuntimeSettings(
            settings.role,
            settings.local,
            settings.key_id,
            settings.secret,
            settings.opponent,
            tmp_path,
        ),
        r7.CONFIG,
        ActorRole.POLICE,
    )
    pregame = composition.pregame
    pregame.milestones.step0_seen.set()

    async def attempt() -> None:
        with pytest.raises(LocalDefectError, match="without an authenticated peer"):
            await boot.await_peer_step0(pregame)

    assert pregame.peer is None
    asyncio.run(attempt())
