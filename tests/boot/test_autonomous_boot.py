"""The permanent boot path: serve, connect, Step-0, one series, stop.

Stage 6C-C1 proved a production `SeriesDriver` plays six sub-games; the shipped
`python -m` process still only served and waited. This is the layer between
them, and it owns **process lifecycle only**: readiness, a bounded outbound
connection, our Step-0, the wait for the peer's, exactly one `play_series`, and
a shutdown that runs whatever happened.

Every gameplay decision stays where 6C-C1 put it. The tests below therefore
assert *sequence and ownership*, never a move, an outcome or a cadence.
"""

import asyncio
import socket
from pathlib import Path

import boot_builders as build
import composed_builders as compose
import pytest
from r16_builders import GROUP_A, GROUP_B

from mars777_police import autonomous_boot as boot
from mars777_police.agent_runtime import AgentRuntime, RuntimeState
from mars777_police.app.protocol_errors import (
    AuthFailureError,
    ConfigMismatchError,
    LocalDefectError,
)
from mars777_police.app.sealed_record_values import ActorRole
from mars777_police.startup_budget import StartupBudget
from mars777_police.transport.wire_errors import TransportFailureError

HOST = build.HOST


def pair() -> tuple[AgentRuntime, AgentRuntime]:
    """Two composed agents pointed at each other, neither started."""
    port_a, port_b = build.pair_urls()
    a = build.agent(GROUP_A, "group_a", ActorRole.POLICE, f"http://{HOST}:{port_b}/mcp")
    b = build.agent(GROUP_B, "group_b", ActorRole.THIEF, f"http://{HOST}:{port_a}/mcp")
    return AgentRuntime(a, HOST, port_a), AgentRuntime(b, HOST, port_b)


def closed_port() -> int:
    """A port bound and released, so nothing is listening on it."""
    with socket.socket() as probe:
        probe.bind((HOST, 0))
        return int(probe.getsockname()[1])


def test_a_closed_port_raises_the_transport_failure_identity() -> None:
    """RED B: the retryable boundary is pinned to what the adapter really raises.

    Not `OSError`, not `httpx.ConnectError`: `PeerClient` translates both into
    the existing local `E-TRANSPORT` category before anything else sees them, so
    that identity - and nothing wider - is what a startup retry may catch.
    """
    composition = build.agent(
        GROUP_A, "group_a", ActorRole.POLICE, f"http://{HOST}:{closed_port()}/mcp"
    )
    runtime = AgentRuntime(composition, HOST, build.free_port())

    async def attempt() -> None:
        await runtime.serve()
        try:
            await runtime.connect()
        finally:
            await runtime.stop()

    with pytest.raises(TransportFailureError):
        asyncio.run(attempt())


def test_a_failed_single_attempt_still_closes_the_runtime() -> None:
    """The historical `connect()` contract is unchanged by the new operation."""
    composition = build.agent(
        GROUP_A, "group_a", ActorRole.POLICE, f"http://{HOST}:{closed_port()}/mcp"
    )
    runtime = AgentRuntime(composition, HOST, build.free_port())

    async def attempt() -> None:
        await runtime.serve()
        with pytest.raises(TransportFailureError):
            await runtime.connect()
        assert runtime.state is RuntimeState.CLOSED

    asyncio.run(attempt())


def test_the_startup_budget_is_bounded_and_stops_the_runtime() -> None:
    """A peer that never appears fails inside the budget, leaving nothing open."""
    composition = build.agent(
        GROUP_A, "group_a", ActorRole.POLICE, f"http://{HOST}:{closed_port()}/mcp"
    )
    runtime = AgentRuntime(composition, HOST, build.free_port())
    budget = StartupBudget(total_seconds=0.5, pause_seconds=0.05)

    async def attempt() -> None:
        await runtime.serve()
        with pytest.raises(TransportFailureError):
            await runtime.connect_until_ready(budget)
        assert runtime.state is RuntimeState.CLOSED

    asyncio.run(attempt())


def test_only_a_transport_failure_is_retried() -> None:
    """Auth, config and protocol refusals are answers, not unavailability."""
    budget = StartupBudget(total_seconds=1.0, pause_seconds=0.01)
    assert budget.retryable(TransportFailureError("E-TRANSPORT")) is True
    for refusal in (AuthFailureError("E-AUTH-FAILURE"), ConfigMismatchError("E-CONFIG-MISMATCH")):
        assert budget.retryable(refusal) is False


def test_a_peer_that_appears_late_is_still_joined(tmp_path: Path) -> None:
    """The startup race, deterministically: the listener opens mid-budget."""
    a, b = pair()
    budget = StartupBudget(total_seconds=10.0, pause_seconds=0.05)

    async def run() -> None:
        await a.serve()

        async def open_the_peer_late() -> None:
            await asyncio.sleep(0.2)
            await b.serve()

        late = asyncio.create_task(open_the_peer_late())
        try:
            await a.connect_until_ready(budget)
            assert a.state is RuntimeState.RUNNING
        finally:
            await late
            await a.stop()
            await b.stop()

    asyncio.run(run())


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


def test_boot_owns_no_gameplay_vocabulary() -> None:
    """The coordinator sequences owners; it never decides anything they own."""
    import inspect

    source = inspect.getsource(boot)
    for forbidden in (
        "MoveAction",
        "BarrierAction",
        "Outcome.",
        "choose_action",
        "close_turn",
        "close_sub_game",
        "send_config_proposal",
        "send_config_lock",
        "adopt_config",
        "open_result_agreement",
        "respond_to_result",
        "legal_moves",
    ):
        assert forbidden not in source


def test_a_budget_must_be_positive_in_both_directions() -> None:
    """A non-positive bound or cadence is a local defect, not a fast retry."""
    for total, pause in ((0.0, 0.1), (1.0, 0.0), (-1.0, 0.1)):
        with pytest.raises(LocalDefectError, match="must be positive"):
            StartupBudget(total_seconds=total, pause_seconds=pause)


def test_the_startup_variant_refuses_a_runtime_that_is_not_serving() -> None:
    """Same precondition as `connect`: there is nothing to connect from."""
    composition = build.agent(
        GROUP_A, "group_a", ActorRole.POLICE, f"http://{HOST}:{closed_port()}/mcp"
    )
    runtime = AgentRuntime(composition, HOST, build.free_port())
    budget = StartupBudget(total_seconds=1.0, pause_seconds=0.05)

    async def attempt() -> None:
        with pytest.raises(LocalDefectError, match="cannot connect while NEW"):
            await runtime.connect_until_ready(budget)

    asyncio.run(attempt())


def test_a_signalled_step0_without_a_peer_is_refused(tmp_path: Path) -> None:
    """The event says *when*; `pregame.peer` is the fact, and boot re-reads it."""
    import r7_builders as r7

    from mars777_police.autonomous_boot import AutonomousBoot
    from mars777_police.infra.settings import RuntimeSettings

    composition = build.agent(
        GROUP_A, "group_a", ActorRole.POLICE, f"http://{HOST}:{closed_port()}/mcp"
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
